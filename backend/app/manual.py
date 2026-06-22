import re
from copy import deepcopy
from collections import defaultdict

from .db import get_conn


ENGINE_ORDER = ("1.6 16V", "1.9 JTD 8V")
SECTION_ORDER = (
    "TECHNICAL DATA",
    "DESCRIPTIONS",
    "FAULT DIAGNOSIS",
    "TEST",
    "PROCEDURES",
    "ELECTRICAL EQUIPMENT",
)
SYSTEM_CATEGORY = re.compile(r"^\d{2}(?:\s|$)")
MANUAL_CODE = re.compile(r"^(\d{4})(?:\s|$)")


def breadcrumb_parts(value):
    return [part.strip() for part in (value or "").split(" > ") if part.strip()]


def page_bucket(page):
    parts = breadcrumb_parts(page.get("breadcrumb"))
    if len(parts) < 4 or parts[2] not in ENGINE_ORDER:
        return None
    engine, section = parts[2], parts[3]
    category = next((part for part in parts[4:] if SYSTEM_CATEGORY.match(part)), None)
    if not category:
        category = parts[4] if len(parts) > 4 else "General"
    return engine, section, category


def build_manual_tree(pages, child_edges):
    page_map = {page["id"]: dict(page) for page in pages}
    buckets = {}
    for page in page_map.values():
        bucket = page_bucket(page)
        if bucket:
            buckets[page["id"]] = bucket

    children = defaultdict(set)
    for parent_id, child_id in child_edges:
        if parent_id in page_map and child_id in page_map:
            children[parent_id].add(child_id)
    for page in page_map.values():
        parent_id = page.get("parent_page_id")
        if parent_id in page_map:
            children[parent_id].add(page["id"])

    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for page_id, (engine, section, category) in buckets.items():
        grouped[engine][section][category].append(page_id)

    def node_for(page_id, allowed, path):
        page = page_map[page_id]
        child_ids = sorted(
            (child for child in children.get(page_id, ()) if child in allowed and child not in path),
            key=lambda child: page_map[child]["title"].lower(),
        )
        child_nodes = [node_for(child, allowed, path | {page_id}) for child in child_ids]
        return {
            "id": page_id,
            "title": page["title"],
            "breadcrumb": page.get("breadcrumb"),
            "category": page.get("category"),
            "image_count": page.get("image_count", 0),
            "child_count": len(child_nodes),
            "kind": "index" if child_nodes else "article",
            "children": child_nodes,
        }

    engines = []
    for engine in ENGINE_ORDER:
        sections = []
        section_names = sorted(
            grouped[engine],
            key=lambda value: (SECTION_ORDER.index(value) if value in SECTION_ORDER else len(SECTION_ORDER), value),
        )
        for section in section_names:
            categories = []
            for category in sorted(grouped[engine][section]):
                ids = set(grouped[engine][section][category])
                incoming = {
                    child
                    for parent in ids
                    for child in children.get(parent, ())
                    if child in ids
                }
                roots = sorted(ids - incoming, key=lambda page_id: page_map[page_id]["title"].lower())
                if not roots:
                    roots = sorted(ids, key=lambda page_id: page_map[page_id]["title"].lower())
                nodes = [node_for(page_id, ids, set()) for page_id in roots]
                categories.append({"title": category, "page_count": len(ids), "pages": nodes})
            sections.append({
                "title": section,
                "page_count": sum(item["page_count"] for item in categories),
                "categories": categories,
            })
        engines.append({
            "title": engine,
            "page_count": sum(item["page_count"] for item in sections),
            "sections": sections,
        })
    def walk(nodes):
        for node in nodes:
            yield node
            yield from walk(node.get("children", []))

    def manual_code(node):
        for part in reversed(breadcrumb_parts(node.get("breadcrumb"))):
            match = MANUAL_CODE.match(part)
            if match:
                return match.group(1)
        return None

    for engine in engines:
        descriptions = next((section for section in engine["sections"] if section["title"] == "DESCRIPTIONS"), None)
        technical = next((section for section in engine["sections"] if section["title"] == "TECHNICAL DATA"), None)
        if not descriptions or not technical:
            continue
        description_children = {}
        for category in descriptions["categories"]:
            for node in walk(category["pages"]):
                code = manual_code(node)
                if code and node.get("children"):
                    description_children[(category["title"], code)] = node["children"]
        for category in technical["categories"]:
            for node in list(walk(category["pages"])):
                code = manual_code(node)
                related = description_children.get((category["title"], code))
                if not related:
                    continue
                existing = {child["id"] for child in node.get("children", [])}
                additions = []
                for child in related:
                    if child["id"] not in existing:
                        copy = deepcopy(child)
                        copy["relation"] = "breadcrumb cross-reference from DESCRIPTIONS"
                        additions.append(copy)
                if additions:
                    node["children"].extend(additions)
                    node["child_count"] = len(node["children"])
                    node["kind"] = "index"
    return {"vehicle": "Fiat Multipla", "page_count": len(buckets), "engines": engines}


def multipla_manual_tree():
    with get_conn() as conn:
        pages = conn.execute("""
            SELECT p.id,p.title,p.breadcrumb,p.category,p.parent_page_id,
                   count(i.id)::int AS image_count
            FROM elearn_pages p
            JOIN vehicles v ON v.id=p.vehicle_id AND v.source_code='186'
            LEFT JOIN elearn_images i ON i.elearn_page_id=p.id AND i.local_path IS NOT NULL
            GROUP BY p.id ORDER BY p.id
        """).fetchall()
        edges = conn.execute("""
            SELECT DISTINCT l.from_page_id,l.discovered_page_id
            FROM elearn_links l
            JOIN elearn_pages p ON p.id=l.from_page_id
            JOIN vehicles v ON v.id=p.vehicle_id AND v.source_code='186'
            WHERE l.link_type='child' AND l.discovered_page_id IS NOT NULL
        """).fetchall()
    return build_manual_tree(pages, [(edge["from_page_id"], edge["discovered_page_id"]) for edge in edges])
