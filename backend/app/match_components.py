import re
from .db import get_conn

def snippet(text, term):
    m = re.search(re.escape(term), text or "", re.I)
    if not m:
        return term
    start, end = max(0, m.start()-80), min(len(text), m.end()+80)
    return text[start:end].replace("\n", " ")

def match():
    made = 0
    with get_conn() as conn:
        comps = conn.execute("SELECT * FROM components").fetchall()
        for comp in comps:
            aliases = [comp["name"]] + [r["alias"] for r in conn.execute("SELECT alias FROM component_aliases WHERE component_id=%s", (comp["id"],)).fetchall()]
            pages = conn.execute("SELECT id, title, breadcrumb, content_text FROM elearn_pages WHERE vehicle_id=%s", (comp["vehicle_id"],)).fetchall()
            for page in pages:
                hay = "\n".join([page.get("title") or "", page.get("breadcrumb") or "", page.get("content_text") or ""])
                for term in aliases:
                    if re.search(r"\b" + re.escape(term) + r"\b", hay, re.I):
                        score = 100 if re.search(re.escape(term), page.get("title") or "", re.I) else 80 if re.search(re.escape(term), page.get("breadcrumb") or "", re.I) else 50
                        conn.execute("""
                            INSERT INTO component_page_links(component_id, elearn_page_id, match_type, match_score, matched_text)
                            VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
                        """, (comp["id"], page["id"], "keyword", score, snippet(hay, term)))
                        made += 1
    return {"matches_attempted": made}

if __name__ == "__main__":
    print(match())
