from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .db import get_conn
from .search import search_pages
from .manual import multipla_manual_tree
from .disc_api import router as disc_router

app = FastAPI(title="Fiat Multipla eLearn MVP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
app.include_router(disc_router)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/vehicles")
def vehicles():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM vehicles ORDER BY make, model").fetchall()

@app.get("/api/vehicles/fiat-multipla")
def multipla():
    with get_conn() as conn:
        vehicle = conn.execute("SELECT * FROM vehicles WHERE source_code='186'").fetchone()
        if not vehicle:
            raise HTTPException(404, "Multipla not found; run migrations")
        stats = conn.execute("""
            SELECT COUNT(*) pages,
                   (SELECT COUNT(*) FROM elearn_images i JOIN elearn_pages p ON p.id=i.elearn_page_id WHERE p.vehicle_id=%s) images,
                   (SELECT COUNT(*) FROM components WHERE vehicle_id=%s) components
            FROM elearn_pages WHERE vehicle_id=%s
        """, (vehicle["id"], vehicle["id"], vehicle["id"])).fetchone()
        return {"vehicle": vehicle, "stats": stats}

@app.get("/api/search")
def api_search(q: str = Query("", min_length=0), limit: int = 20):
    return search_pages(q, limit)

@app.get("/api/manual/fiat-multipla/tree")
@app.get("/manual/fiat-multipla/tree")
def manual_tree():
    return multipla_manual_tree()

@app.get("/api/elearn/{page_id}")
def elearn_page(page_id: int):
    with get_conn() as conn:
        page = conn.execute("SELECT * FROM elearn_pages WHERE id=%s", (page_id,)).fetchone()
        if not page:
            raise HTTPException(404, "Page not found")
        images = conn.execute("SELECT * FROM elearn_images WHERE elearn_page_id=%s ORDER BY id", (page_id,)).fetchall()
        links = conn.execute("SELECT * FROM elearn_links WHERE from_page_id=%s ORDER BY id", (page_id,)).fetchall()
        child_pages = conn.execute("""
            SELECT id, title, source_url, breadcrumb, category
            FROM elearn_pages WHERE parent_page_id=%s
            UNION
            SELECT p.id, p.title, p.source_url, p.breadcrumb, p.category
            FROM elearn_links l JOIN elearn_pages p ON p.id=l.discovered_page_id
            WHERE l.from_page_id=%s AND l.link_type='child'
            ORDER BY title
        """, (page_id, page_id)).fetchall()
        source_child_links = conn.execute("""
            SELECT link_text, to_url AS source_url
            FROM elearn_links
            WHERE from_page_id=%s AND link_type='child' AND discovered_page_id IS NULL
            ORDER BY link_text
        """, (page_id,)).fetchall()
        return {
            "page": page,
            "images": images,
            "links": links,
            "child_pages": child_pages,
            "source_child_links": source_child_links,
        }

@app.get("/api/components")
def components():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT c.*, COALESCE(json_agg(a.alias ORDER BY a.alias) FILTER (WHERE a.alias IS NOT NULL), '[]') aliases,
                   COUNT(DISTINCT l.elearn_page_id) related_pages
            FROM components c
            LEFT JOIN component_aliases a ON a.component_id=c.id
            LEFT JOIN component_page_links l ON l.component_id=c.id
            GROUP BY c.id ORDER BY c.name
        """).fetchall()
        return rows

@app.get("/api/components/{slug}")
def component(slug: str):
    with get_conn() as conn:
        comp = conn.execute("SELECT * FROM components WHERE slug=%s", (slug,)).fetchone()
        if not comp:
            raise HTTPException(404, "Component not found")
        aliases = conn.execute("SELECT alias FROM component_aliases WHERE component_id=%s ORDER BY alias", (comp["id"],)).fetchall()
        pages = conn.execute("""
            SELECT l.match_type, l.match_score, l.matched_text, p.id, p.title, p.breadcrumb, p.category, p.source_url,
                   (SELECT json_agg(json_build_object('image_url', image_url, 'local_path', local_path, 'alt_text', alt_text)) FROM elearn_images i WHERE i.elearn_page_id=p.id) images
            FROM component_page_links l JOIN elearn_pages p ON p.id=l.elearn_page_id
            WHERE l.component_id=%s ORDER BY l.match_score DESC, p.title LIMIT 50
        """, (comp["id"],)).fetchall()
        return {"component": comp, "aliases": aliases, "pages": pages}
