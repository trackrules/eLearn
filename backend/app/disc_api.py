"""Read-only preview API for the isolated eLearn disc staging release."""

from __future__ import annotations

import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response

from .db import get_conn
from .disc_renderer import UnsafeXmlError, render_xml, sanitize_svg_bytes


router = APIRouter(prefix="/disc", tags=["disc-preview"])
ASSET_ID = re.compile(r"^[0-9]+$")
DISC_ASSET_DIR = Path(os.getenv("DISC_ASSET_DIR", "/disc-assets"))


def _read_only(conn):
    conn.execute("SET TRANSACTION READ ONLY")
    release = conn.execute("""
        SELECT * FROM disc_staging.source_release
        WHERE status='complete' AND model_code='186' AND language_id=2
        ORDER BY imported_at DESC, id DESC LIMIT 1
    """).fetchone()
    if not release:
        raise HTTPException(503, "No complete English Multipla disc staging release")
    return release


def _applicability(conn, release_id: int, subject: str, source_id: int):
    if subject not in {"element", "xml"}:
        raise ValueError("invalid applicability subject")
    id_column = f"source_{subject}_id"
    rows = conn.execute(f"""
        SELECT a.applicability_type,a.applicability_id,
               COALESCE(p.name,v.name,c.name) name,
               COALESCE(p.code,v.code,c.code) code
        FROM disc_staging.disc_{subject}_applicability a
        LEFT JOIN disc_staging.disc_production p ON a.release_id=p.release_id
          AND a.applicability_type='production' AND a.applicability_id=p.source_production_id
        LEFT JOIN disc_staging.disc_validity v ON a.release_id=v.release_id
          AND a.applicability_type='validity' AND a.applicability_id=v.source_validity_id
        LEFT JOIN disc_staging.disc_codep c ON a.release_id=c.release_id
          AND a.applicability_type='codep' AND a.applicability_id=c.source_codep_id
        WHERE a.release_id=%s AND a.{id_column}=%s
        ORDER BY a.applicability_type,a.applicability_id
    """, (release_id, source_id)).fetchall()
    grouped = {"production": [], "validity": [], "codep": []}
    for row in rows:
        grouped[row["applicability_type"]].append({
            "id": row["applicability_id"], "name": row["name"], "code": row["code"]
        })
    return grouped


def build_manual_tree(sections, elements):
    children = defaultdict(list)
    by_id = {row["source_element_id"]: row for row in elements}
    for row in elements:
        children[row["parent_element_id"]].append(row)
    for group in children.values():
        group.sort(key=lambda row: (row.get("orders") is None, row.get("orders") or 0, row["name"], row["source_element_id"]))

    def node(row, trail):
        element_id = row["source_element_id"]
        if element_id in trail:
            return {"element_id": element_id, "name": row["name"], "cycle": True}
        return {
            "element_id": element_id,
            "element_ref": f"/disc/elements/{element_id}",
            "name": row["name"], "code": row.get("code"), "orders": row.get("orders"),
            "xml_count": row.get("xml_count", 0),
            "children": [node(child, trail | {element_id}) for child in children.get(element_id, [])],
        }

    result = []
    for section in sorted(sections, key=lambda row: row["section_type"]):
        root = by_id.get(section["root_element_id"])
        result.append({
            "section_id": section["source_section_id"], "section_type": section["section_type"],
            "name": section["name"], "root_element_id": section["root_element_id"],
            "root": node(root, set()) if root else None,
        })
    return result


def _asset_file(asset_id: str) -> Path:
    if not ASSET_ID.fullmatch(asset_id):
        raise HTTPException(400, "Asset ID must contain digits only")
    return DISC_ASSET_DIR / f"{asset_id}.image"


@router.get("/health")
def disc_health():
    with get_conn() as conn:
        release = _read_only(conn)
        counts = conn.execute("""
            SELECT
              (SELECT count(*) FROM disc_staging.disc_section WHERE release_id=%s) sections,
              (SELECT count(*) FROM disc_staging.disc_element WHERE release_id=%s) elements,
              (SELECT count(*) FROM disc_staging.disc_xml WHERE release_id=%s) xml_records,
              (SELECT count(*) FROM disc_staging.disc_asset WHERE release_id=%s) assets,
              (SELECT count(*) FROM disc_staging.disc_asset WHERE release_id=%s AND NOT exists_on_disc) missing_assets
        """, (release["id"],) * 5).fetchone()
        return {"ok": True, "read_only": True, "release": release, "counts": counts,
                "asset_directory_available": DISC_ASSET_DIR.is_dir()}


@router.get("/manual/fiat-multipla/tree")
def disc_manual_tree():
    with get_conn() as conn:
        release = _read_only(conn)
        sections = conn.execute("""SELECT * FROM disc_staging.disc_section
          WHERE release_id=%s ORDER BY section_type""", (release["id"],)).fetchall()
        elements = conn.execute("""
          SELECT e.*,count(x.source_xml_id) xml_count
          FROM disc_staging.disc_element e
          LEFT JOIN disc_staging.disc_xml x ON x.release_id=e.release_id
            AND x.source_element_id=e.source_element_id
          WHERE e.release_id=%s GROUP BY e.release_id,e.source_element_id
          ORDER BY e.source_section_id,e.orders,e.source_element_id
        """, (release["id"],)).fetchall()
        return {"release_key": release["release_key"], "sections": build_manual_tree(sections, elements)}


@router.get("/elements/{element_id}")
def disc_element(element_id: int):
    with get_conn() as conn:
        release = _read_only(conn)
        element = conn.execute("""
          SELECT e.*,s.name section_name,s.section_type
          FROM disc_staging.disc_element e JOIN disc_staging.disc_section s
            ON s.release_id=e.release_id AND s.source_section_id=e.source_section_id
          WHERE e.release_id=%s AND e.source_element_id=%s
        """, (release["id"], element_id)).fetchone()
        if not element:
            raise HTTPException(404, "Disc element not found")
        children = conn.execute("""SELECT source_element_id,name,code,orders
          FROM disc_staging.disc_element WHERE release_id=%s AND parent_element_id=%s
          ORDER BY orders NULLS LAST,name""", (release["id"], element_id)).fetchall()
        xml_records = conn.execute("""SELECT source_xml_id,orders,normalized_text_sha256
          FROM disc_staging.disc_xml WHERE release_id=%s AND source_element_id=%s
          ORDER BY orders NULLS LAST,source_xml_id""", (release["id"], element_id)).fetchall()
        return {
            "release_key": release["release_key"], "element": element,
            "parent_ref": f"/disc/elements/{element['parent_element_id']}" if element["parent_element_id"] else None,
            "children": [{**row, "element_ref": f"/disc/elements/{row['source_element_id']}"} for row in children],
            "xml_records": [{**row, "xml_ref": f"/disc/xml/{row['source_xml_id']}"} for row in xml_records],
            "applicability": _applicability(conn, release["id"], "element", element_id),
        }


@router.get("/xml/{xml_id}")
def disc_xml(xml_id: int):
    with get_conn() as conn:
        release = _read_only(conn)
        record = conn.execute("""
          SELECT x.*,e.name element_name,e.code element_code,s.name section_name,s.section_type
          FROM disc_staging.disc_xml x JOIN disc_staging.disc_element e
            ON e.release_id=x.release_id AND e.source_element_id=x.source_element_id
          JOIN disc_staging.disc_section s
            ON s.release_id=e.release_id AND s.source_section_id=e.source_section_id
          WHERE x.release_id=%s AND x.source_xml_id=%s
        """, (release["id"], xml_id)).fetchone()
        if not record:
            raise HTTPException(404, "Disc XML record not found")
        try:
            rendered = render_xml(record["raw_xml"])
        except UnsafeXmlError as exc:
            raise HTTPException(422, f"Disc XML failed safe rendering: {exc}") from exc
        links = conn.execute("""SELECT ordinal,target_id,target_code,target_description,link_kind
          FROM disc_staging.disc_content_link WHERE release_id=%s AND source_xml_id=%s ORDER BY ordinal""",
          (release["id"], xml_id)).fetchall()
        assets = conn.execute("""SELECT ca.ordinal,ca.source_asset_id,ca.reference_kind,
            a.exists_on_disc,a.detected_type,a.byte_size,a.byte_sha256
          FROM disc_staging.disc_content_asset ca JOIN disc_staging.disc_asset a
            ON a.release_id=ca.release_id AND a.source_asset_id=ca.source_asset_id
          WHERE ca.release_id=%s AND ca.source_xml_id=%s ORDER BY ca.ordinal""",
          (release["id"], xml_id)).fetchall()
        return {
            "release_key": release["release_key"], "xml": record, "rendered_html": rendered,
            "element_ref": f"/disc/elements/{record['source_element_id']}",
            "links": [{**row, "target_ref": (
                f"/disc/elements/{row['target_id']}" if row["link_kind"] == "resolved_element" else None
            )} for row in links],
            "assets": [{**row, "asset_ref": f"/disc/assets/{row['source_asset_id']}"} for row in assets],
            "applicability": _applicability(conn, release["id"], "xml", xml_id),
        }


@router.get("/assets/{asset_id}")
def disc_asset(asset_id: str):
    path = _asset_file(asset_id)
    with get_conn() as conn:
        release = _read_only(conn)
        asset = conn.execute("""SELECT * FROM disc_staging.disc_asset
          WHERE release_id=%s AND source_asset_id=%s""", (release["id"], asset_id)).fetchone()
        if not asset:
            raise HTTPException(404, "Disc asset ID not found")
    if not asset["exists_on_disc"]:
        return JSONResponse(status_code=404, content={"ok": False, "placeholder": True,
            "error": {"code": "disc_asset_missing", "message": "Asset is referenced but absent from the disc"},
            "asset": {"asset_id": asset_id, "detected_type": asset["detected_type"]}})
    if not path.is_file():
        return JSONResponse(status_code=503, content={"ok": False, "placeholder": True,
            "error": {"code": "disc_asset_storage_unavailable", "message": "Read-only disc asset mount is unavailable"},
            "asset": {"asset_id": asset_id, "detected_type": asset["detected_type"]}})
    data = path.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if asset["byte_sha256"] and actual_hash.lower() != asset["byte_sha256"].lower():
        return JSONResponse(status_code=409, content={"ok": False, "placeholder": True,
            "error": {"code": "disc_asset_hash_mismatch", "message": "Asset failed integrity validation"},
            "asset": {"asset_id": asset_id}})
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"}
    if asset["detected_type"] == "JPEG":
        return FileResponse(path, media_type="image/jpeg", headers=headers, filename=None)
    if asset["detected_type"] in {"SVG", "gzipped SVG"}:
        try:
            safe_svg = sanitize_svg_bytes(data, compressed=asset["detected_type"] == "gzipped SVG")
        except UnsafeXmlError as exc:
            headers["Content-Disposition"] = f'attachment; filename="{asset_id}.image"'
            headers["X-Disc-Asset-Safety"] = "attachment-only"
            return Response(data, media_type="application/octet-stream", headers=headers)
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
        return Response(safe_svg, media_type="image/svg+xml", headers=headers)
    headers["Content-Disposition"] = f'attachment; filename="{asset_id}.image"'
    return Response(data, media_type="application/octet-stream", headers=headers)


@router.get("/search")
def disc_search(q: str = Query("", max_length=200), limit: int = Query(20, ge=1, le=100)):
    query = " ".join(q.split())
    if not query:
        return {"query": "", "count": 0, "results": []}
    pattern = f"%{query}%"
    with get_conn() as conn:
        release = _read_only(conn)
        rows = conn.execute("""
          SELECT x.source_xml_id,x.source_element_id,e.name element_name,e.code element_code,
                 s.name section_name,s.section_type,left(COALESCE(x.full_text,x.normalized_text),500) excerpt
          FROM disc_staging.disc_xml x JOIN disc_staging.disc_element e
            ON e.release_id=x.release_id AND e.source_element_id=x.source_element_id
          JOIN disc_staging.disc_section s
            ON s.release_id=e.release_id AND s.source_section_id=e.source_section_id
          WHERE x.release_id=%s AND (e.name ILIKE %s OR e.code ILIKE %s
            OR x.full_text ILIKE %s OR x.normalized_text ILIKE %s)
          ORDER BY CASE WHEN e.name ILIKE %s THEN 0 WHEN e.code ILIKE %s THEN 1 ELSE 2 END,
                   s.section_type,e.name,x.source_xml_id LIMIT %s
        """, (release["id"], pattern, pattern, pattern, pattern, pattern, pattern, limit)).fetchall()
        return {"query": query, "count": len(rows), "results": [{**row,
            "element_ref": f"/disc/elements/{row['source_element_id']}",
            "xml_ref": f"/disc/xml/{row['source_xml_id']}"} for row in rows]}
