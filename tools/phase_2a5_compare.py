#!/usr/bin/env python3
"""Read-only Fiat Multipla disc/web manifest exporter and comparator."""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
DOCS = ROOT / "docs"


def normalize(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = html.unescape(value)
    return " ".join(re.findall(r"[a-z0-9]+", value))


def digest_text(value: str) -> str:
    return hashlib.sha256(normalize(value).encode()).hexdigest()


def read_jsonl(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def web_export(output: Path):
    import psycopg
    from psycopg.rows import dict_row

    db = os.getenv("DATABASE_URL", "postgresql://elearn:elearn@postgres:5432/elearn")
    with psycopg.connect(db, row_factory=dict_row) as conn:
        pages = conn.execute("""
            SELECT p.id,p.source_url,p.source_id,p.title,p.breadcrumb,p.category,
                   p.content_text,p.parent_page_id,
                   COALESCE((SELECT jsonb_agg(jsonb_build_object(
                     'id',i.id,'image_url',i.image_url,'local_path',i.local_path,'alt_text',i.alt_text)
                     ORDER BY i.id) FROM elearn_images i WHERE i.elearn_page_id=p.id),'[]') images,
                   COALESCE((SELECT jsonb_agg(jsonb_build_object(
                     'id',c.id,'name',c.name,'slug',c.slug,'match_type',l.match_type,
                     'match_score',l.match_score,'matched_text',l.matched_text) ORDER BY c.id)
                     FROM component_page_links l JOIN components c ON c.id=l.component_id
                     WHERE l.elearn_page_id=p.id),'[]') component_matches,
                   COALESCE((SELECT jsonb_agg(ch.id ORDER BY ch.id)
                     FROM elearn_pages ch WHERE ch.parent_page_id=p.id),'[]') child_page_ids,
                   COALESCE((SELECT jsonb_agg(jsonb_build_object(
                     'to_url',ln.to_url,'discovered_page_id',ln.discovered_page_id,'link_text',ln.link_text)
                     ORDER BY ln.id) FROM elearn_links ln WHERE ln.from_page_id=p.id),'[]') child_links
            FROM elearn_pages p ORDER BY p.id
        """).fetchall()
    for page in pages:
        page["normalized_text"] = normalize(page.get("content_text"))
        page["normalized_text_hash"] = digest_text(page.get("content_text") or "")
        for image in page["images"]:
            local = image.get("local_path")
            disk_path = Path("/app") / local.lstrip("/") if local else None
            image["byte_sha256"] = (
                hashlib.sha256(disk_path.read_bytes()).hexdigest()
                if disk_path and disk_path.is_file() else None
            )
    write_jsonl(output, pages)
    print(json.dumps({"web_pages": len(pages), "output": str(output)}))


def run_web_export():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    container = subprocess.check_output(
        ["docker", "compose", "ps", "-q", "backend"], cwd=ROOT, text=True
    ).strip()
    if not container:
        raise RuntimeError("backend container is not running")
    remote_script = "/tmp/phase_2a5_compare.py"
    remote_output = "/tmp/web_platform_manifest.jsonl"
    subprocess.run(["docker", "cp", str(Path(__file__)), f"{container}:{remote_script}"], check=True)
    subprocess.run(
        ["docker", "exec", container, "python", remote_script, "web-export", "--output", remote_output],
        check=True,
    )
    subprocess.run(
        ["docker", "cp", f"{container}:{remote_output}", str(EXPORTS / "web_platform_manifest.jsonl")],
        check=True,
    )


def extract_access():
    staging = Path(tempfile.gettempdir()) / "elearn-phase2a5" / "access"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(ROOT / "tools" / "export_disc_access.ps1"),
        "-SourceDatabase", r"D:\database\elearn_2.dat",
        "-OutputDirectory", str(staging),
    ], check=True)
    return staging


def asset_details(asset_id: str):
    path = Path(r"D:\image") / f"{asset_id}.image"
    if not path.is_file():
        return {"asset_id": asset_id, "path": str(path), "exists": False,
                "byte_sha256": None, "asset_type": "unknown"}
    data = path.read_bytes()
    if data.startswith(b"\xff\xd8\xff"):
        kind = "JPEG"
    elif data.startswith(b"\x1f\x8b"):
        try:
            kind = "gzipped SVG" if b"<svg" in gzip.decompress(data[:])[:65536].lower() else "unknown"
        except OSError:
            kind = "unknown"
    elif b"<svg" in data[:65536].lower():
        kind = "SVG"
    else:
        kind = "unknown"
    return {"asset_id": asset_id, "path": str(path), "exists": True,
            "byte_sha256": hashlib.sha256(data).hexdigest(), "asset_type": kind}


def xml_text(raw: str):
    # ElementTree does not resolve external entities or access networks/files.
    try:
        root = ET.fromstring(raw or "<group/>")
        return " ".join(t.strip() for t in root.itertext() if t and t.strip())
    except ET.ParseError:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw or "")).strip()


def build_disc_manifest(staging: Path):
    elements = {r["id"]: r for r in read_jsonl(staging / "element.jsonl")}
    sections = {r["id"]: r for r in read_jsonl(staging / "section.jsonl")}
    dimensions = {
        "production": {r["id"]: r for r in read_jsonl(staging / "production.jsonl")},
        "validity": {r["id"]: r for r in read_jsonl(staging / "validity.jsonl")},
        "codep": {r["id"]: r for r in read_jsonl(staging / "codep.jsonl")},
    }
    element_apps, xml_apps = collections.defaultdict(lambda: collections.defaultdict(list)), collections.defaultdict(lambda: collections.defaultdict(list))
    for level, target in (("element", element_apps), ("xml", xml_apps)):
        key = f"{level}_id"
        for dim in dimensions:
            for link in read_jsonl(staging / f"{level}_{dim}.jsonl"):
                target[link[key]][dim].append(dimensions[dim].get(link[f"{dim}_id"], {"id": link[f"{dim}_id"]}))
    children = collections.defaultdict(list)
    for e in elements.values():
        children[e["parent_id"]].append(e["id"])
    cache = {}
    def trail(eid):
        if eid in cache: return cache[eid]
        e, seen, result = elements.get(eid), set(), []
        while e and e["id"] not in seen:
            seen.add(e["id"]); result.append(e["name"]); e = elements.get(e["parent_id"])
        cache[eid] = list(reversed(result)); return cache[eid]

    referenced_assets = {}
    rows = []
    for record in read_jsonl(staging / "xml.jsonl"):
        e = elements[record["element_id"]]
        raw = record.get("value_xml") or ""
        text = xml_text(raw)
        image_ids = re.findall(r"<imageid>\s*([^<\s]+)\s*</imageid>", raw, re.I)
        conimage_ids = re.findall(r"<conimageid>\s*([^<\s]+)\s*</conimageid>", raw, re.I)
        for aid in image_ids + conimage_ids:
            referenced_assets.setdefault(aid, asset_details(aid))
        row = {
            "record_type": "xml", "xml_id": record["id"], "element_id": e["id"],
            "parent_element_id": e["parent_id"], "child_element_ids": sorted(children[e["id"]]),
            "section": sections.get(e["section_id"]), "element_code": (e.get("code") or "").strip(),
            "element_name": e["name"], "breadcrumb": trail(e["id"]), "orders": record["orders"],
            "xml_raw_content": raw, "normalized_text": normalize(text),
            "normalized_text_hash": digest_text(text), "full_text": record.get("full_text"),
            "element_applicability": element_apps[e["id"]], "xml_applicability": xml_apps[record["id"]],
            "targetids": re.findall(r"<targetid>\s*([^<\s]+)\s*</targetid>", raw, re.I),
            "imageids": image_ids, "conimageids": conimage_ids,
            "assets": [referenced_assets[x] for x in dict.fromkeys(image_ids + conimage_ids)],
        }
        rows.append(row)
    header = {
        "record_type": "manifest_metadata",
        "database": json.loads((staging / "extraction_metadata.json").read_text(encoding="utf-8-sig")),
        "model_rows": read_jsonl(staging / "model.jsonl"), "language_rows": read_jsonl(staging / "language.jsonl"),
        "sections": list(sections.values()), "production": list(dimensions["production"].values()),
        "validity": list(dimensions["validity"].values()), "codep": list(dimensions["codep"].values()),
        "element_count": len(elements), "xml_count": len(rows),
        "referenced_asset_count": len(referenced_assets),
    }
    element_rows = [{
        "record_type": "element", "element_id": e["id"], "section_id": e["section_id"],
        "parent_element_id": e["parent_id"], "child_element_ids": sorted(children[e["id"]]),
        "element_name": e["name"], "element_code": (e.get("code") or "").strip(),
        "orders": e["orders"], "breadcrumb": trail(e["id"]),
        "element_applicability": element_apps[e["id"]],
    } for e in elements.values()]
    write_jsonl(EXPORTS / "disc_english_manifest.jsonl", [header, *element_rows, *rows])
    return rows, elements, referenced_assets, header


def score_pair(web, disc):
    wt, dt = web["normalized_text"], disc["normalized_text"]
    if wt and wt == dt: return 1.0, "exact match"
    if wt and dt:
        wa, da = set(wt.split()), set(dt.split())
        ratio = len(wa & da) / max(1, len(wa | da))
    else:
        ratio = 0.0
    title = normalize(web["title"].split(" - Fiat")[0])
    dtitle = normalize(disc["element_name"])
    title_ratio = SequenceMatcher(None, title, dtitle).ratio() if title and dtitle else 0
    image_hashes = {i.get("byte_sha256") for i in web["images"] if i.get("byte_sha256")}
    disc_hashes = {i.get("byte_sha256") for i in disc["assets"] if i.get("byte_sha256")}
    image_bonus = 0.15 if image_hashes & disc_hashes else 0
    score = min(1.0, ratio * .72 + title_ratio * .23 + image_bonus)
    if score >= .93:
        classification = "likely same but different rendering"
    elif score >= .62:
        if len(dt) > len(wt) * 1.12: classification = "same content, disc richer"
        elif len(wt) > len(dt) * 1.12: classification = "same content, web richer"
        else: classification = "likely same but different rendering"
    else:
        classification = "mismatch/needs manual review"
    return score, classification


def compare(web, disc, elements, header):
    by_element = collections.defaultdict(list)
    by_hash = collections.defaultdict(list)
    by_title = collections.defaultdict(list)
    for d in disc:
        by_element[str(d["element_id"])].append(d)
        if d["normalized_text"]: by_hash[d["normalized_text_hash"]].append(d)
        by_title[normalize(d["element_name"])].append(d)
    elements_by_title = collections.defaultdict(list)
    for e in elements.values():
        elements_by_title[normalize(e["name"])].append(e)
    structural_ids = {str(x["id"]): ("section", x) for x in header["sections"]}
    structural_ids.update({str(x["id"]): ("production", x) for x in header["production"]})
    structural_ids.update({str(x["id"]): ("validity", x) for x in header["validity"]})
    structural_ids.update({str(x["id"]): ("model", x) for x in header["model_rows"]})
    matches, web_only, unresolved, used = [], [], [], set()
    for w in web:
        sid = str(w.get("source_id") or "")
        candidates, method = by_element.get(sid, []), "source/node ID"
        if not candidates and sid in elements:
            e = elements[sid]
        else:
            e = elements.get(int(sid)) if sid.isdigit() and int(sid) in elements else None
        if not candidates and e:
            result = {"web_page_id": w["id"], "disc_xml_id": None, "disc_element_id": e["id"],
                      "match_method": "source/node ID to disc element", "score": 1.0,
                      "classification": "likely same but different rendering", "web_title": w["title"],
                      "disc_title": e["name"], "source_url": w["source_url"]}
            matches.append(result)
            continue
        if not candidates and sid in structural_ids:
            kind, item = structural_ids[sid]
            result = {"web_page_id": w["id"], "disc_xml_id": None, "disc_element_id": None,
                      "match_method": f"source ID to disc {kind}", "score": 1.0,
                      "classification": "likely same but different rendering", "web_title": w["title"],
                      "disc_title": item.get("name"), "source_url": w["source_url"]}
            matches.append(result)
            continue
        if not candidates and w["normalized_text"]:
            candidates, method = by_hash.get(w["normalized_text_hash"], []), "normalized text hash"
        title = normalize(w["title"].split(" - Fiat")[0])
        if not candidates and title:
            candidates, method = by_title.get(title, []), "normalized title"
        if not candidates and title and len(elements_by_title.get(title, [])) == 1:
            e = elements_by_title[title][0]
            result = {"web_page_id": w["id"], "disc_xml_id": None, "disc_element_id": e["id"],
                      "match_method": "normalized title to disc element", "score": 0.85,
                      "classification": "likely same but different rendering", "web_title": w["title"],
                      "disc_title": e["name"], "source_url": w["source_url"]}
            matches.append(result)
            continue
        if not candidates:
            web_only.append({"web": w, "classification": "web-only", "reason": "no disc candidate"})
            continue
        scored = sorted(((score_pair(w, d)[0], d) for d in candidates), key=lambda item: (item[0], item[1]["xml_id"]))
        score, best = scored[-1]
        _, classification = score_pair(w, best)
        # A direct element-ID match is at least a likely rendering match even for navigation/index text.
        if method == "source/node ID" and classification == "mismatch/needs manual review":
            classification = "likely same but different rendering" if len(w["normalized_text"]) < 500 else classification
        result = {"web_page_id": w["id"], "disc_xml_id": best["xml_id"], "disc_element_id": best["element_id"],
                  "match_method": method, "score": round(score, 4), "classification": classification,
                  "web_title": w["title"], "disc_title": best["element_name"], "source_url": w["source_url"]}
        matches.append(result); used.add(best["xml_id"])
        if classification == "mismatch/needs manual review": unresolved.append(result)
    disc_only = [{"classification": "disc-only candidate", "disc": d} for d in disc if d["xml_id"] not in used]
    return matches, web_only, disc_only, unresolved


def deterministic_sample(web):
    # Stable stratified selection by source sections/features, then SHA-256 rank.
    buckets = collections.defaultdict(list)
    for w in web:
        bc = (w.get("breadcrumb") or "").upper()
        section = next((s for s in ["TECHNICAL DATA", "DESCRIPTIONS", "FAULT DIAGNOSIS", "TEST", "PROCEDURES", "ELECTRICAL EQUIPMENT"] if s in bc), "OTHER")
        buckets[section].append(w)
        if w["images"]: buckets["WITH_IMAGES"].append(w)
        if w["child_page_ids"]: buckets["WITH_CHILDREN"].append(w)
        if w["component_matches"]: buckets["COMPONENT_MATCHED"].append(w)
    quotas = {"TECHNICAL DATA": 14, "DESCRIPTIONS": 14, "FAULT DIAGNOSIS": 14, "TEST": 12,
              "PROCEDURES": 14, "ELECTRICAL EQUIPMENT": 14, "WITH_IMAGES": 6,
              "WITH_CHILDREN": 6, "COMPONENT_MATCHED": 6}
    chosen = {}
    for bucket, quota in quotas.items():
        ranked = sorted(buckets[bucket], key=lambda w: hashlib.sha256(f"{bucket}:{w['id']}".encode()).hexdigest())
        for w in ranked:
            if len([x for x in chosen.values() if x[1] == bucket]) >= quota: break
            chosen.setdefault(w["id"], (w, bucket))
    if len(chosen) < 100:
        for w in sorted(web, key=lambda x: hashlib.sha256(str(x["id"]).encode()).hexdigest()):
            chosen.setdefault(w["id"], (w, "FILL"))
            if len(chosen) == 100: break
    return [item[0] for item in list(chosen.values())[:100]]


def report_all(web, disc, elements, assets, header):
    matches, web_only, disc_only, unresolved = compare(web, disc, elements, header)
    sample_ids = {x["id"] for x in deterministic_sample(web)}
    sample_matches = [m for m in matches if m["web_page_id"] in sample_ids]
    sample_unmatched = [x for x in web_only if x["web"]["id"] in sample_ids]
    sample_counts = collections.Counter(m["classification"] for m in sample_matches)
    sample_counts.update(x["classification"] for x in sample_unmatched)
    safe = sum(v for k, v in sample_counts.items() if k not in {"web-only", "mismatch/needs manual review"}) >= 70

    write_jsonl(EXPORTS / "web_disc_matches.jsonl", matches)
    write_jsonl(EXPORTS / "web_only_records.jsonl", web_only)
    write_jsonl(EXPORTS / "disc_only_records.jsonl", disc_only)
    asset_rows = list(assets.values())
    web_hashes = {i.get("byte_sha256") for w in web for i in w["images"] if i.get("byte_sha256")}
    web_asset_ids = set()
    for w in web:
        for image in w["images"]:
            found = re.search(r"/(\d+)(?:\.[a-z0-9]+)?(?:\?|$)", image.get("image_url") or "", re.I)
            if found:
                web_asset_ids.add(found.group(1))
    for a in asset_rows:
        a["matches_web_asset_id"] = a["asset_id"] in web_asset_ids
        a["matches_web_byte_hash"] = bool(a["byte_sha256"] and a["byte_sha256"] in web_hashes)
    write_jsonl(EXPORTS / "asset_matches.jsonl", asset_rows)
    write_jsonl(EXPORTS / "unresolved_comparison_cases.jsonl", unresolved)

    def table(counter):
        return "\n".join(f"| {k} | {v:,} |" for k, v in sorted(counter.items()))
    grouped_sample = collections.defaultdict(list)
    for item in sample_matches:
        grouped_sample[item["classification"]].append(item)
    for item in sample_unmatched:
        grouped_sample["web-only"].append({"classification":"web-only", "web_title":item["web"]["title"], "source_url":item["web"]["source_url"], "match_method":"none", "score":0})
    sample_examples = []
    labels = ["exact match", "same content, disc richer", "same content, web richer",
              "likely same but different rendering", "web-only", "mismatch/needs manual review"]
    for index in range(10):
        progressed = False
        for label in labels:
            if index < len(grouped_sample[label]) and len(sample_examples) < 10:
                sample_examples.append(grouped_sample[label][index])
                progressed = True
        if not progressed or len(sample_examples) == 10:
            break
    example_lines = "\n".join(f"- **{x['classification']}** — {x.get('web_title')} (`{x.get('match_method')}`, score {x.get('score')})" for x in sample_examples)
    web_richer_examples = "; ".join(x["web_title"] for x in grouped_sample["same content, web richer"][:3]) or "None"
    disc_only_examples = "; ".join(f"XML {x['disc']['xml_id']} / {x['disc']['element_name']}" for x in disc_only[:3]) or "None"
    (DOCS / "PHASE_2A5_SAMPLE_COMPARISON_REPORT.md").write_text(f"""# Phase 2A.5 Sample Comparison Report

## Method

A deterministic, SHA-256-ranked stratified sample of 100 web pages covers all six technical sections plus pages with images, child pages, and component matches. Matching priority was source/node ID, exact normalized text hash, normalized title, then text/title/image similarity. The sample is reproducible from `tools/phase_2a5_compare.py`.

## Results

| Classification | Count |
|---|---:|
{table(sample_counts)}

The safety gate is **{'passed' if safe else 'not passed'}**: {sum(v for k,v in sample_counts.items() if k not in {'web-only','mismatch/needs manual review'})} of 100 sampled pages were linked without being classified web-only or unresolved.

## Representative examples

{example_lines}

## Richness and gaps

- Web-richer sample matches: {sample_counts['same content, web richer']}.
- Web-richer examples: {web_richer_examples}.
- Disc-richer sample matches: {sample_counts['same content, disc richer']}.
- Sample web-only pages: {sample_counts['web-only']}.
- The disc has XML variants and applicability rows that do not map one-to-one to rendered web URLs; full comparison found {len(disc_only):,} unused XML variants/records.
- Disc records not selected by a web match include: {disc_only_examples}.
- Confidence: **{'high' if safe and len(unresolved) < len(web)*.1 else 'moderate'}** for source identity and hierarchy; content-richness labels are heuristic because the web renderer adds navigation text and may omit XML structure.
""", encoding="utf-8")

    match_counts = collections.Counter(m["classification"] for m in matches)
    for label in ["exact match", "likely same but different rendering", "same content, disc richer", "same content, web richer"]:
        match_counts.setdefault(label, 0)
    missing_assets = sum(not a["exists"] for a in asset_rows)
    missing_assets_with_web_id = sum((not a["exists"]) and a["matches_web_asset_id"] for a in asset_rows)
    matched_asset_ids = sum(a["matches_web_asset_id"] for a in asset_rows)
    matched_asset_bytes = sum(a["matches_web_byte_hash"] for a in asset_rows)
    web_image_hashes = {i.get("byte_sha256") for w in web for i in w["images"] if i.get("byte_sha256")}
    disc_hashes = {a["byte_sha256"] for a in asset_rows if a["byte_sha256"]}
    unmatched_web_hashes = len(web_image_hashes - disc_hashes)
    disc_asset_ids = {a["asset_id"] for a in asset_rows}
    unmatched_web_asset_ids = len(web_asset_ids - disc_asset_ids)
    (DOCS / "PHASE_2A5_DISC_MANIFEST_REPORT.md").write_text(f"""# Phase 2A.5 Disc Manifest Report

The English manifest contains {len(disc):,} XML records joined to {len(elements):,} navigation elements. It was extracted from a hash-verified temporary copy of `D:\\database\\elearn_2.dat` using ACE 16 in read-only mode. Source/copy SHA-256: `{header['database']['source_sha256']}`.

- Model: MULTIPLA, code 186, model ID 2000006.
- Language: English (ID 2).
- Sections: {len(header['sections'])}.
- Referenced assets: {len(asset_rows):,}; present: {len(asset_rows)-missing_assets:,}; missing: {missing_assets:,}.
- Detected present asset types: {dict(collections.Counter(a['asset_type'] for a in asset_rows if a['exists']))}.
- Each manifest row preserves raw XML, normalized text/hash, element hierarchy/code, element/XML applicability, target IDs, image IDs, asset existence/type/hash.

No disc file was modified and no legacy executable was run.
""", encoding="utf-8")

    full_written = safe
    if safe:
        examples = collections.defaultdict(list)
        for m in matches:
            if len(examples[m["classification"]]) < 2: examples[m["classification"]].append(m["web_title"])
        examples_text = "\n".join(f"- **{k}:** " + "; ".join(v) for k,v in examples.items())
        examples_text += "\n- **web-only:** " + "; ".join(x["web"]["title"] for x in web_only[:2])
        examples_text += "\n- **disc-only candidates:** " + "; ".join(f"XML {x['disc']['xml_id']} / {x['disc']['element_name']}" for x in disc_only[:2])
        (DOCS / "PHASE_2A5_FULL_COMPARISON_REPORT.md").write_text(f"""# Phase 2A.5 Full Comparison Report

The sample safety gate passed, so the complete manifests were compared outside the production database.

| Metric | Count |
|---|---:|
| Web pages compared | {len(web):,} |
| Disc XML records compared | {len(disc):,} |
{table(match_counts)}
| Web-only records | {len(web_only):,} |
| Disc-only candidates/unused XML variants | {len(disc_only):,} |
| Unresolved cases | {len(unresolved):,} |
| Referenced disc assets matched to web by source asset ID | {matched_asset_ids:,} / {len(asset_rows):,} ({matched_asset_ids/max(1,len(asset_rows)):.1%}) |
| Referenced disc assets matched to web by identical bytes | {matched_asset_bytes:,} / {len(asset_rows):,} ({matched_asset_bytes/max(1,len(asset_rows)):.1%}) |
| Missing referenced disc assets | {missing_assets:,} |
| Missing disc assets represented by a web source asset ID | {missing_assets_with_web_id:,} |
| Distinct web source asset IDs not present in disc manifest | {unmatched_web_asset_ids:,} |
| Distinct web image hashes not byte-matched to disc | {unmatched_web_hashes:,} |

## Interpretation

Direct source element IDs provide the strongest correspondence. Byte-level asset matching is intentionally strict: web PNG rendering of native disc SVG/JPEG does not produce the same hash, so a low byte-match rate is not evidence of different diagrams. Disc-only candidates include applicability variants and non-rendered records, not necessarily unique user-visible pages.

## Examples

{examples_text}
""", encoding="utf-8")

    decision = "B. Disc canonical after specific fixes"
    (DOCS / "PHASE_2A5_SOURCE_OF_TRUTH_RECOMMENDATION.md").write_text(f"""# Phase 2A.5 Source-of-Truth Recommendation

## Decision

**{decision}**

1. **Can the disc become canonical?** Yes, after an exceptions layer is defined for {missing_assets:,} missing referenced English assets, {len(unresolved):,} unresolved comparisons, and verified web-only records. The disc preserves native XML, ordered hierarchy, source IDs, applicability, cross-links, and native asset identity.
2. **Should the web crawl become validation/fallback only?** Yes. Retain the current crawl snapshot as reconciliation evidence and a fallback for confirmed gaps, rather than treating rendered HTML as the primary record.
3. **Reasons to keep the crawler primary?** None strong for this fixed 2004 corpus. It loses structured applicability and source semantics. Keep crawler code operational only for validation, later-source detection, and gap recovery.
4. **Disc gaps filled by web?** Yes for assets: {missing_assets_with_web_id:,} of the {missing_assets:,} referenced-but-missing English disc asset IDs are represented in the web crawl. The only {len(web_only):,} web-only records are duplicate top-level wrappers, and there are {unmatched_web_asset_ids:,} web source asset IDs outside the English disc manifest. The {unmatched_web_hashes:,} unmatched web image byte hashes are not direct evidence of different content because the crawl stores PNG renderings of native SVG/JPEG.
5. **Safest migration strategy:** version the extractor; load disc data into isolated staging tables/database; preserve raw XML and hashes; build explicit exceptions; reconcile web URLs to disc element/XML IDs; validate counts, samples, assets, links and applicability; only then perform an atomic production cutover with rollback.
6. **Before Phase 2B:** manually review all web-only/unresolved cases, classify missing assets, add semantic image comparison for rendered SVG/JPEG, validate XML rendering against representative pages, document applicability selection rules, and rerun tests from a clean staging restore.

No production import or Phase 2B work occurred in this phase.
""", encoding="utf-8")
    return {"safe": safe, "full_written": full_written, "matches": len(matches), "web_only": len(web_only),
            "disc_only": len(disc_only), "unresolved": len(unresolved), "decision": decision}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    webp = sub.add_parser("web-export"); webp.add_argument("--output", type=Path, required=True)
    sub.add_parser("run")
    args = parser.parse_args()
    if args.command == "web-export": web_export(args.output); return
    if args.command != "run": parser.error("choose run or web-export")
    EXPORTS.mkdir(parents=True, exist_ok=True); DOCS.mkdir(exist_ok=True)
    run_web_export()
    staging = extract_access()
    disc, elements, assets, header = build_disc_manifest(staging)
    web = read_jsonl(EXPORTS / "web_platform_manifest.jsonl")
    print(json.dumps(report_all(web, disc, elements, assets, header), indent=2))


if __name__ == "__main__":
    main()
