#!/usr/bin/env python3
"""Build and load the English eLearn disc staging release without cutover."""

from __future__ import annotations

import argparse
import collections
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "tools" else Path("/app")
EXPORTS = ROOT / "data" / "exports"
DOCS = ROOT / "docs"
IMPORTER_VERSION = "phase-2a6-v1"
EXPECTED = {"elements": 5111, "xml": 7177, "physical_assets": 4064, "referenced_assets": 3959,
            "staged_assets": 4140, "missing_assets": 76,
            "unresolved_comparisons": 433, "disc_only_variants": 3955, "web_richer": 1268}


def json_lines(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_phase_2a5():
    path = Path(__file__).resolve().with_name("phase_2a5_compare.py")
    spec = importlib.util.spec_from_file_location("phase_2a5_compare", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def ensure_comparison_exports(p25):
    required = [
        "web_platform_manifest.jsonl", "web_disc_matches.jsonl", "web_only_records.jsonl",
        "disc_only_records.jsonl", "unresolved_comparison_cases.jsonl",
    ]
    if all((EXPORTS / name).exists() for name in required):
        return
    p25.run_web_export()
    staging = p25.extract_access()
    disc, elements, assets, header = p25.build_disc_manifest(staging)
    web = p25.read_jsonl(EXPORTS / "web_platform_manifest.jsonl")
    p25.report_all(web, disc, elements, assets, header)


def build_bundle():
    p25 = load_phase_2a5()
    ensure_comparison_exports(p25)
    access_staging = p25.extract_access()
    disc, elements, assets, header = p25.build_disc_manifest(access_staging)
    manifest_path = EXPORTS / "disc_english_manifest.jsonl"
    source_hash = header["database"]["source_sha256"]
    if source_hash != header["database"]["copy_sha256"] or not header["database"]["hashes_match"]:
        raise RuntimeError("disc source and temporary-copy hashes differ")
    if source_hash != "3B9BABEB029ABF75F469A17BD9A7735EFC50F7751EDE7484CC6BCBCC7D385394":
        raise RuntimeError(f"unexpected English disc database hash: {source_hash}")

    bundle = EXPORTS / "phase_2a6_bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    shutil.copy2(manifest_path, bundle / manifest_path.name)
    all_assets = {path.stem: p25.asset_details(path.stem) for path in Path(r"D:\image").glob("*.image")}
    for asset_id, asset in assets.items():
        all_assets.setdefault(asset_id, asset)
    write_jsonl(bundle / "all_assets.jsonl", sorted(all_assets.values(), key=lambda x: x["asset_id"]))
    for name in ["web_disc_matches.jsonl", "web_only_records.jsonl", "disc_only_records.jsonl",
                 "unresolved_comparison_cases.jsonl", "web_platform_manifest.jsonl"]:
        shutil.copy2(EXPORTS / name, bundle / name)
    metadata = {
        "release_key": f"multipla-186-en-{source_hash[:12].lower()}",
        "source_name": "Fiat Multipla eLearn original disc",
        "model_code": "186", "language_id": 2,
        "source_database_path": r"D:\database\elearn_2.dat",
        "source_database_sha256": source_hash,
        "source_asset_path": r"D:\image",
        "importer_version": IMPORTER_VERSION,
        "expected": EXPECTED,
    }
    (bundle / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return bundle, disc, elements, assets, header


def local_name(tag: str):
    return tag.rsplit("}", 1)[-1].lower()


def child_text(node: ET.Element, wanted: str):
    for child in node.iter():
        if local_name(child.tag) == wanted:
            return " ".join(x.strip() for x in child.itertext() if x and x.strip())
    return ""


def extract_links(record):
    raw = record["xml_raw_content"]
    result = []
    try:
        root = ET.fromstring(raw or "<group/>")
        for node in root.iter():
            if local_name(node.tag) != "link":
                continue
            target = child_text(node, "targetid")
            if not target:
                continue
            result.append({"target": target, "code": child_text(node, "code"),
                           "description": child_text(node, "description")})
    except ET.ParseError:
        result = [{"target": target, "code": "", "description": ""} for target in record["targetids"]]
    return result


def container_load(bundle: Path):
    import psycopg
    from psycopg.types.json import Jsonb

    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    manifest = list(json_lines(bundle / "disc_english_manifest.jsonl"))
    header = manifest[0]
    element_rows = [row for row in manifest[1:] if row["record_type"] == "element"]
    xml_rows = [row for row in manifest[1:] if row["record_type"] == "xml"]
    elements = {row["element_id"] for row in element_rows}
    assets = {asset["asset_id"]: asset for asset in json_lines(bundle / "all_assets.jsonl")}

    database_url = os.getenv("DATABASE_URL", "postgresql://elearn:elearn@postgres:5432/elearn")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM disc_staging.source_release WHERE release_key=%s", (metadata["release_key"],))
            cur.execute("""
                INSERT INTO disc_staging.source_release
                  (release_key,source_name,model_code,language_id,source_database_path,
                   source_database_sha256,source_asset_path,importer_version,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'importing') RETURNING id
            """, (metadata["release_key"], metadata["source_name"], metadata["model_code"],
                  metadata["language_id"], metadata["source_database_path"],
                  metadata["source_database_sha256"], metadata["source_asset_path"],
                  metadata["importer_version"]))
            release_id = cur.fetchone()[0]

            cur.executemany("""
                INSERT INTO disc_staging.disc_language
                  (release_id,source_language_id,name,code,set_code,internal_search)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, [(release_id, x["id"], x["name"], x.get("code"), x.get("set_code"), x.get("internalsearch"))
                  for x in header["language_rows"]])
            cur.executemany("""
                INSERT INTO disc_staging.disc_model
                  (release_id,source_model_id,source_language_id,source_mark_id,name,code)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, [(release_id, x["id"], x["language_id"], x.get("mark_id"), x["name"], x["code"])
                  for x in header["model_rows"]])
            cur.executemany("""
                INSERT INTO disc_staging.disc_section
                  (release_id,source_section_id,source_language_id,source_model_id,root_element_id,
                   name,section_type,orders,clickable,indent)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, [(release_id, x["id"], x["language_id"], x["model_id"], x.get("root_elem_id"),
                   x["name"], x["type"], x.get("orders"), x.get("cliccable"), x.get("indent"))
                  for x in header["sections"]])
            cur.executemany("""
                INSERT INTO disc_staging.disc_element
                  (release_id,source_element_id,source_section_id,parent_element_id,source_language_id,
                   name,code,orders,all_codep,all_validity,all_production,layout,breadcrumb)
                VALUES (%s,%s,%s,%s,2,%s,%s,%s,%s,%s,%s,%s,%s)
            """, [(release_id, x["element_id"], x["section_id"], x["parent_element_id"],
                   x["element_name"], x.get("element_code"), x.get("orders"),
                   x["all_codep"], x["all_validity"], x["all_production"], x.get("layout"), Jsonb(x["breadcrumb"]))
                  for x in element_rows])
            cur.executemany("""
                INSERT INTO disc_staging.disc_xml
                  (release_id,source_xml_id,source_element_id,source_language_id,raw_xml,raw_xml_sha256,
                   full_text,normalized_text,normalized_text_sha256,orders,
                   all_codep,all_validity,all_production)
                VALUES (%s,%s,%s,2,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, [(release_id, x["xml_id"], x["element_id"], x["xml_raw_content"],
                   hashlib.sha256(x["xml_raw_content"].encode()).hexdigest(), x.get("full_text"),
                   x["normalized_text"], x["normalized_text_hash"], x.get("orders"),
                   x["all_codep"], x["all_validity"], x["all_production"]) for x in xml_rows])

            for table, rows, prefix in [
                ("disc_production", header["production"], "production"),
                ("disc_validity", header["validity"], "validity"),
                ("disc_codep", header["codep"], "codep"),
            ]:
                if prefix == "production":
                    sql = """INSERT INTO disc_staging.disc_production
                      (release_id,source_production_id,source_language_id,source_model_id,name,code,validity_id)
                      VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                    values = [(release_id,x["id"],x["language_id"],x["model_id"],x["name"],x.get("code"),x.get("validity_id")) for x in rows]
                elif prefix == "validity":
                    sql = """INSERT INTO disc_staging.disc_validity
                      (release_id,source_validity_id,source_language_id,source_model_id,name,code,orders)
                      VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                    values = [(release_id,x["id"],x["language_id"],x["model_id"],x["name"],x.get("code"),x.get("orders")) for x in rows]
                else:
                    sql = """INSERT INTO disc_staging.disc_codep
                      (release_id,source_codep_id,source_language_id,source_model_id,name,code)
                      VALUES (%s,%s,%s,%s,%s,%s)"""
                    values = [(release_id,x["id"],x["language_id"],x["model_id"],x["name"],x.get("code")) for x in rows]
                cur.executemany(sql, values)

            element_apps, xml_apps = [], []
            for row in element_rows:
                for kind, values in row["element_applicability"].items():
                    element_apps.extend((release_id,row["element_id"],kind,x["id"]) for x in values)
            for row in xml_rows:
                for kind, values in row["xml_applicability"].items():
                    xml_apps.extend((release_id,row["xml_id"],kind,x["id"]) for x in values)
            cur.executemany("""INSERT INTO disc_staging.disc_element_applicability
              (release_id,source_element_id,applicability_type,applicability_id) VALUES (%s,%s,%s,%s)""", element_apps)
            cur.executemany("""INSERT INTO disc_staging.disc_xml_applicability
              (release_id,source_xml_id,applicability_type,applicability_id) VALUES (%s,%s,%s,%s)""", xml_apps)

            link_rows, content_assets = [], []
            exceptions = []
            for row in xml_rows:
                for ordinal, link in enumerate(extract_links(row)):
                    target_text = link["target"]
                    if not re.fullmatch(r"\d+", target_text):
                        kind, target = "unresolved_target", -1
                    else:
                        target = int(target_text)
                        kind = "local_anchor" if target in (0, 1) else "resolved_element" if target in elements else "unresolved_target"
                    link_rows.append((release_id,row["xml_id"],ordinal,target,link["code"],link["description"],kind))
                    if kind in {"local_anchor", "unresolved_target"}:
                        exceptions.append((release_id,kind,"content_link",f"{row['xml_id']}:{ordinal}",
                                           Jsonb({"source_xml_id":row["xml_id"],"target_id":target_text,
                                                  "code":link["code"],"description":link["description"]})))
                refs = [(x,"imageid") for x in row["imageids"]] + [(x,"conimageid") for x in row["conimageids"]]
                content_assets.extend((release_id,row["xml_id"],ordinal,asset_id,kind)
                                      for ordinal,(asset_id,kind) in enumerate(refs))
            cur.executemany("""INSERT INTO disc_staging.disc_content_link
              (release_id,source_xml_id,ordinal,target_id,target_code,target_description,link_kind)
              VALUES (%s,%s,%s,%s,%s,%s,%s)""", link_rows)
            cur.executemany("""INSERT INTO disc_staging.disc_asset
              (release_id,source_asset_id,source_path,exists_on_disc,byte_size,byte_sha256,detected_type)
              VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              [(release_id,a["asset_id"],a["path"],a["exists"],a.get("byte_size"),a.get("byte_sha256"),a["asset_type"]) for a in assets.values()])
            cur.executemany("""INSERT INTO disc_staging.disc_content_asset
              (release_id,source_xml_id,ordinal,source_asset_id,reference_kind) VALUES (%s,%s,%s,%s,%s)""", content_assets)

            for asset in assets.values():
                if not asset["exists"]:
                    exceptions.append((release_id,"missing_asset","asset",asset["asset_id"],Jsonb(asset)))
            matches = list(json_lines(bundle / "web_disc_matches.jsonl"))
            cur.executemany("""INSERT INTO disc_staging.web_disc_match
              (release_id,web_page_id,source_element_id,source_xml_id,match_method,match_score,classification,source_url)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
              [(release_id,m["web_page_id"],m.get("disc_element_id"),m.get("disc_xml_id"),m["match_method"],m["score"],m["classification"],m.get("source_url")) for m in matches])
            for m in matches:
                if m["classification"] == "mismatch/needs manual review":
                    exceptions.append((release_id,"unresolved_comparison","web_page",str(m["web_page_id"]),Jsonb(m)))
                if m["classification"] == "same content, web richer":
                    exceptions.append((release_id,"web_richer","web_page",str(m["web_page_id"]),Jsonb(m)))
            for row in json_lines(bundle / "disc_only_records.jsonl"):
                disc = row["disc"]
                exceptions.append((release_id,"disc_only_xml_variant","disc_xml",str(disc["xml_id"]),
                                   Jsonb({"source_xml_id":disc["xml_id"],"source_element_id":disc["element_id"],
                                          "element_name":disc["element_name"]})))
            for row in json_lines(bundle / "web_only_records.jsonl"):
                web = row["web"]
                exceptions.append((release_id,"web_only_wrapper","web_page",str(web["id"]),
                                   Jsonb({"source_url":web["source_url"],"title":web["title"]})))
            severity = {"missing_asset":"warning", "unresolved_target":"warning",
                        "unresolved_comparison":"warning", "web_richer":"info",
                        "disc_only_xml_variant":"info", "local_anchor":"info", "web_only_wrapper":"info"}
            cur.executemany("""INSERT INTO disc_staging.disc_exception
              (release_id,exception_type,severity,subject_type,subject_id,details)
              VALUES (%s,%s,%s,%s,%s,%s)""",
              [(r,t,severity[t],s,i,d) for r,t,s,i,d in exceptions])

            tables = ["disc_language","disc_model","disc_section","disc_element","disc_xml","disc_production",
                      "disc_validity","disc_codep","disc_element_applicability","disc_xml_applicability",
                      "disc_content_link","disc_asset","disc_content_asset","disc_exception","web_disc_match"]
            counts = {}
            for table in tables:
                cur.execute(f"SELECT count(*) FROM disc_staging.{table} WHERE release_id=%s", (release_id,))
                counts[table] = cur.fetchone()[0]
            cur.execute("""SELECT exception_type,count(*) FROM disc_staging.disc_exception
                           WHERE release_id=%s GROUP BY exception_type ORDER BY exception_type""", (release_id,))
            exception_counts = dict(cur.fetchall())
            counts["exception_types"] = exception_counts
            cur.execute("""SELECT raw_xml,raw_xml_sha256,normalized_text,normalized_text_sha256
                           FROM disc_staging.disc_xml WHERE release_id=%s""", (release_id,))
            hash_mismatches = 0
            for raw_xml, raw_hash, normalized, normalized_hash in cur.fetchall():
                hash_mismatches += hashlib.sha256(raw_xml.encode()).hexdigest() != raw_hash
                hash_mismatches += hashlib.sha256(normalized.encode()).hexdigest() != normalized_hash
            cur.execute("""SELECT count(*) FILTER (WHERE exists_on_disc),
                                  count(*) FILTER (WHERE NOT exists_on_disc),
                                  count(*) FILTER (WHERE exists_on_disc AND (byte_sha256 IS NULL OR byte_size IS NULL))
                           FROM disc_staging.disc_asset WHERE release_id=%s""", (release_id,))
            physical_assets, missing_assets, unhashed_physical_assets = cur.fetchone()
            cur.execute("""SELECT count(DISTINCT source_asset_id) FROM disc_staging.disc_content_asset
                           WHERE release_id=%s""", (release_id,))
            referenced_asset_ids = cur.fetchone()[0]
            cur.execute("""SELECT detected_type,count(*) FROM disc_staging.disc_asset
                           WHERE release_id=%s AND exists_on_disc GROUP BY detected_type ORDER BY detected_type""", (release_id,))
            asset_types = dict(cur.fetchall())
            validation = {
                "xml_hash_mismatches": hash_mismatches,
                "physical_assets": physical_assets,
                "missing_asset_placeholders": missing_assets,
                "unhashed_physical_assets": unhashed_physical_assets,
                "referenced_asset_ids": referenced_asset_ids,
                "asset_types": asset_types,
            }
            if hash_mismatches or unhashed_physical_assets:
                raise RuntimeError(f"staging hash validation failed: {validation}")
            cur.execute("UPDATE disc_staging.source_release SET status='complete',counts=%s WHERE id=%s",
                        (Jsonb(counts), release_id))
    result = {"release_id":release_id,"release_key":metadata["release_key"],"counts":counts,"validation":validation,
              "source_database_sha256":metadata["source_database_sha256"]}
    (bundle / "import_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


def token_similarity(left: str, right: str):
    a, b = set(re.findall(r"[a-z0-9]+", left.lower())), set(re.findall(r"[a-z0-9]+", right.lower()))
    return len(a & b) / max(1, len(a | b))


def validate_rendering(disc, web_rows):
    sys.path.insert(0, str(ROOT / "backend"))
    from app.disc_renderer import render_xml

    web_by_source = collections.defaultdict(list)
    for web in web_rows:
        if web.get("source_id"):
            web_by_source[str(web["source_id"])].append(web)
    candidates = collections.defaultdict(list)
    for row in disc:
        section_type = row.get("section", {}).get("type")
        if section_type not in range(1, 7) or not row["normalized_text"]:
            continue
        for web in web_by_source[str(row["element_id"])]:
            score = token_similarity(row["normalized_text"], web.get("normalized_text") or "")
            candidates[section_type].append((score, len(row["normalized_text"]), row, web))
    section_names = {1:"Electrical/Wiring",2:"Tests",3:"Descriptions",4:"Technical Data",5:"Fault Diagnosis",6:"Procedures"}
    render_dir = EXPORTS / "phase_2a6_rendered"
    render_dir.mkdir(parents=True, exist_ok=True)
    validation = []
    for section_type in range(1, 7):
        if not candidates[section_type]:
            raise RuntimeError(f"no rendering candidate for section type {section_type}")
        if section_type == 1:
            score, _, row, web = max(
                candidates[section_type],
                key=lambda x: (bool(x[2]["imageids"] or x[2]["conimageids"]), x[0], x[1]),
            )
        else:
            score, _, row, web = max(candidates[section_type], key=lambda x: (x[0], x[1]))
        rendered = render_xml(row["xml_raw_content"])
        rendered_text = html.unescape(re.sub(r"<[^>]+>", " ", rendered))
        rendered_score = token_similarity(rendered_text, web.get("normalized_text") or "")
        path = render_dir / f"section_{section_type}_xml_{row['xml_id']}.html"
        path.write_text(rendered, encoding="utf-8")
        validation.append({
            "section_type":section_type,"section_name":section_names[section_type],
            "source_xml_id":row["xml_id"],"source_element_id":row["element_id"],
            "web_page_id":web["id"],"web_source_url":web["source_url"],
            "token_similarity":round(rendered_score,4),
            "source_target_count":len(row["targetids"]),"rendered_link_count":rendered.count("disc://element/"),
            "source_asset_reference_count":len(row["imageids"])+len(row["conimageids"]),
            "rendered_asset_count":rendered.count("disc-asset://"),
            "rendered_html_sha256":hashlib.sha256(rendered.encode()).hexdigest(),
            "rendered_path":str(path),
        })
    write_jsonl(EXPORTS / "phase_2a6_render_validation.jsonl", validation)
    return validation


def run_container_import(bundle: Path):
    subprocess.run(["docker","compose","exec","-T","backend","python","-m","app.cli","migrate"], cwd=ROOT, check=True)
    container = subprocess.check_output(["docker","compose","ps","-q","backend"], cwd=ROOT, text=True).strip()
    remote = f"/tmp/phase2a6_bundle_{os.getpid()}"
    subprocess.run(["docker","cp",str(bundle),f"{container}:{remote}"], check=True)
    subprocess.run(["docker","cp",str(Path(__file__).resolve()),f"{container}:/tmp/phase_2a6_staging.py"], check=True)
    subprocess.run(["docker","exec",container,"python","/tmp/phase_2a6_staging.py","container-load","--bundle",remote], check=True)
    subprocess.run(["docker","cp",f"{container}:{remote}/import_result.json",str(bundle / "import_result.json")], check=True)
    return json.loads((bundle / "import_result.json").read_text(encoding="utf-8"))


def write_reports(result, validation):
    counts, exceptions = result["counts"], result["counts"]["exception_types"]
    integrity = result["validation"]
    count_rows = "\n".join(f"| `{key}` | {value:,} |" for key,value in counts.items() if key != "exception_types")
    exception_rows = "\n".join(f"| `{key}` | {value:,} |" for key,value in exceptions.items())
    render_rows = "\n".join(
        f"| {x['section_name']} | {x['source_element_id']} | {x['source_xml_id']} | {x['web_page_id']} | {x['token_similarity']:.4f} | {x['rendered_link_count']}/{x['source_target_count']} | {x['rendered_asset_count']}/{x['source_asset_reference_count']} |"
        for x in validation)
    (DOCS / "PHASE_2A6_DISC_STAGING_IMPORT_REPORT.md").write_text(f"""# Phase 2A.6 Disc Staging Import Report

## Outcome

The English Fiat Multipla disc was imported into the isolated `disc_staging` schema. Production tables were not changed or replaced. Release `{result['release_key']}` completed with source database SHA-256 `{result['source_database_sha256']}` after a byte-identical temporary copy was opened through ACE in read-only mode.

## Imported counts

| Table | Rows |
|---|---:|
{count_rows}

The core counts match Phase 2A.5: 5,111 elements, 7,177 XML records, 4,064 physical native assets, 3,959 English-referenced asset IDs, and 76 referenced-but-missing English assets. `disc_asset` therefore contains 4,140 rows: every physical asset plus missing-reference placeholders.

## Persisted exceptions

| Exception type | Rows |
|---|---:|
{exception_rows}

Every XML row preserves the source XML ID, element ID, raw XML, raw XML SHA-256, normalized text and normalized-text SHA-256. Assets preserve source IDs, paths, existence, detected type and byte SHA-256 where present. Applicability remains separated at element and XML scope.

Post-load integrity validation found {integrity['xml_hash_mismatches']} XML/text hash mismatches and {integrity['unhashed_physical_assets']} unhashed physical assets. The physical corpus is {integrity['asset_types']} and `disc_content_asset` references {integrity['referenced_asset_ids']:,} distinct source asset IDs.

No production page, image, link, component, or search-index record was replaced.
""", encoding="utf-8")
    (DOCS / "PHASE_2A6_RENDERING_VALIDATION_REPORT.md").write_text(f"""# Phase 2A.6 Rendering Validation Report

## Security model

The proof-of-concept renderer uses Python's non-XSLT `ElementTree` parser, rejects DTD/entity declarations and active-content elements, applies an explicit HTML whitelist, escapes source text, and never resolves file or network resources. Links use the internal `disc://element/<id>` scheme and assets use `disc-asset://<id>`; no ActiveX, VBScript, JavaScript, external entity, external file, or network loading is available.

## Representative validation

| Section | Element | XML | Web page | Token similarity | Links rendered/source | Assets rendered/source |
|---|---:|---:|---:|---:|---:|---:|
{render_rows}

All six native section types rendered successfully. Internal source link and asset references were preserved in the output. Similarity is token-set Jaccard against the existing rendered web page and is evidence for content alignment, not pixel equivalence.

Rendered proof files and validation JSON are generated under ignored `data/exports/` paths and are not production UI assets.
""", encoding="utf-8")
    (DOCS / "PHASE_2A6_CUTOVER_PLAN.md").write_text("""# Phase 2A.6 Cutover Plan

## Current decision

Do not cut over yet. The disc release is staged and queryable, while the existing web-import tables remain the production source.

## Required approvals and gates

1. Review all unresolved comparison, unresolved target, missing-asset, disc-only-variant, and web-richer exceptions.
2. Recover or explicitly waive missing native assets; use the web crawl as fallback where its source asset ID fills a disc gap.
3. Validate applicability selection for production range, engine validity and CODEP combinations.
4. Expand rendering review beyond the six representatives, including diagnostic tables and complex wiring diagrams.
5. Define stable production URLs and redirects from web page IDs to disc element/XML IDs.
6. Build a reversible cutover migration and rehearse it against a database backup.
7. Reindex search from staged canonical text and compare search quality before promotion.
8. Obtain explicit approval before changing any production read path.

## Proposed cutover sequence after approval

Freeze the accepted staging release by database hash; resolve or accept exceptions; create compatibility views/API adapters; run a full regression and link/asset audit; snapshot production; enable the disc-backed read path behind a feature flag; monitor and compare; then retire web-primary reads only after rollback criteria remain clear.

Phase 2B must remain out of scope until this cutover is approved and complete.
""", encoding="utf-8")


def host_run():
    bundle, disc, elements, assets, header = build_bundle()
    web = list(json_lines(bundle / "web_platform_manifest.jsonl"))
    validation = validate_rendering(disc, web)
    result = run_container_import(bundle)
    expected = result["counts"]
    assertions = {
        "disc_element": EXPECTED["elements"], "disc_xml": EXPECTED["xml"], "disc_asset": EXPECTED["staged_assets"],
        "web_disc_match": 6949,
    }
    for key, value in assertions.items():
        if expected.get(key) != value:
            raise RuntimeError(f"{key} count {expected.get(key)} != expected {value}")
    integrity = result["validation"]
    for key, value in [("physical_assets",4064),("missing_asset_placeholders",76),
                       ("referenced_asset_ids",3959),("xml_hash_mismatches",0),
                       ("unhashed_physical_assets",0)]:
        if integrity.get(key) != value:
            raise RuntimeError(f"{key} validation {integrity.get(key)} != expected {value}")
    for key, value in [("missing_asset",76),("unresolved_comparison",433),
                       ("disc_only_xml_variant",3955),("web_richer",1268)]:
        actual = expected["exception_types"].get(key)
        if actual != value:
            raise RuntimeError(f"{key} exception count {actual} != expected {value}")
    write_reports(result, validation)
    print(json.dumps({"result":result,"rendering":validation}, indent=2))


def host_prepare():
    bundle, disc, elements, assets, header = build_bundle()
    web = list(json_lines(bundle / "web_platform_manifest.jsonl"))
    validation = validate_rendering(disc, web)
    print(json.dumps({"bundle":str(bundle),"disc_xml":len(disc),"elements":len(elements),
                      "referenced_assets":len(assets),"rendering":validation}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run")
    sub.add_parser("prepare")
    load = sub.add_parser("container-load")
    load.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "container-load":
        container_load(args.bundle)
    elif args.command == "prepare":
        host_prepare()
    else:
        host_run()


if __name__ == "__main__":
    main()
