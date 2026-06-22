import os
import meilisearch
from .db import get_conn

MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "dev_master_key")
INDEX = "elearn_pages"

def client():
    return meilisearch.Client(MEILI_URL, MEILI_MASTER_KEY)

def rebuild_index():
    c = client()
    idx = c.index(INDEX)
    idx.update_searchable_attributes(["title", "breadcrumb", "category", "content_text", "vehicle"])
    idx.update_filterable_attributes(["vehicle", "category"])
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.title, p.breadcrumb, p.category, p.content_text, p.source_url,
                   v.make || ' ' || v.model AS vehicle
            FROM elearn_pages p JOIN vehicles v ON v.id=p.vehicle_id
            WHERE v.source_code='186'
        """).fetchall()
    docs = [dict(r) for r in rows]
    if docs:
        idx.add_documents(docs, primary_key="id")
    return {"indexed": len(docs)}

def search_pages(q: str, limit: int = 20):
    if q.strip():
        return client().index(INDEX).search(q, {"limit": limit})
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.title, p.breadcrumb, p.category, p.content_text, p.source_url,
                   v.make || ' ' || v.model AS vehicle
            FROM elearn_pages p JOIN vehicles v ON v.id=p.vehicle_id
            ORDER BY p.updated_at DESC LIMIT %s
        """, (limit,)).fetchall()
    return {"hits": rows, "estimatedTotalHits": len(rows), "query": q}
