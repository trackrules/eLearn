import argparse, hashlib, json, os, re, time
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from .db import get_conn

DEFAULT_ROOT = "https://4cardata.info/elearn/186/2/"
ROOT = DEFAULT_ROOT
RATE = float(os.getenv("CRAWL_RATE_SECONDS", "1.0"))
IMG_DIR = os.getenv("IMAGE_STORAGE_DIR", "storage/images")
PUBLIC_IMAGE_PATH = os.getenv("PUBLIC_IMAGE_PATH", "/storage/images")
MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "0"))


def is_multipla_url(url):
    p = urlparse(url)
    return p.netloc == "4cardata.info" and (p.path == "/elearn/186" or p.path.startswith("/elearn/186/"))

def is_multipla_image(url):
    p = urlparse(url)
    return p.netloc == "4cardata.info" and p.path.startswith("/image/schemes/fiat/")

def canonical_url(url):
    parsed = urlparse(url)
    if parsed.netloc == "4cardata.info":
        parsed = parsed._replace(scheme="https")
    return parsed._replace(fragment="").geturl()

def source_id(url):
    qs = parse_qs(urlparse(url).query)
    return qs.get("id", [None])[0] or os.path.basename(urlparse(url).path) or None

def content_node(soup):
    heading = soup.find("h3")
    if heading and heading.parent:
        return heading.parent
    menu = soup.select_one(".list-group")
    if menu:
        return menu
    for selector in ("article", "main", ".col-lg", "#mainContainer"):
        node = soup.select_one(selector)
        if node:
            return node
    return soup

def menu_child_links(soup, page_url):
    links = []
    for anchor in soup.select(".list-group a[href]"):
        url = canonical_url(urljoin(page_url, anchor["href"]))
        if is_multipla_url(url):
            links.append(url)
    return links

def text_of(soup):
    root = content_node(soup)
    lines = []
    for text in root.stripped_strings:
        line = re.sub(r"\s+", " ", text).strip()
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    return "\n".join(lines)

def tables(soup):
    out = []
    for table in content_node(soup).find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells: rows.append(cells)
        if rows: out.append(rows)
    return out

def title(soup, url):
    h = soup.find(["h1", "h2", "h3"])
    if h and h.get_text(strip=True): return h.get_text(" ", strip=True)
    if soup.title and soup.title.string: return soup.title.string.strip()
    return url

def breadcrumb(soup):
    crumbs = []
    for sel in [".breadcrumb", "#breadcrumb", ".path"]:
        node = soup.select_one(sel)
        if node: crumbs.append(node.get_text(" > ", strip=True))
    if crumbs: return crumbs[0]
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"], limit=4)]
    return " > ".join([h for h in headings if h])

def upsert_page(conn, vehicle_id, url, html, soup, parent_id):
    bc = breadcrumb(soup)
    cat = bc.split(">", 1)[0].strip() if bc else None
    row = conn.execute("""
        INSERT INTO elearn_pages(vehicle_id, source_url, source_id, title, breadcrumb, category, raw_html, content_text, tables_json, parent_page_id)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (source_url) DO UPDATE SET title=EXCLUDED.title, breadcrumb=EXCLUDED.breadcrumb, category=EXCLUDED.category,
          raw_html=EXCLUDED.raw_html, content_text=EXCLUDED.content_text, tables_json=EXCLUDED.tables_json,
          parent_page_id=COALESCE(elearn_pages.parent_page_id, EXCLUDED.parent_page_id), updated_at=now()
        RETURNING id
    """, (vehicle_id, url, source_id(url), title(soup, url), bc, cat, html, text_of(soup), json.dumps(tables(soup)), parent_id)).fetchone()
    return row["id"]

def reconcile_existing_pages():
    pending = []
    with get_conn() as conn:
        pages = conn.execute("SELECT id, source_url, raw_html FROM elearn_pages ORDER BY id").fetchall()
        imported = {canonical_url(page["source_url"]): page["id"] for page in pages}
        for page in pages:
            soup = BeautifulSoup(page["raw_html"], "html.parser")
            conn.execute(
                "UPDATE elearn_pages SET content_text=%s, tables_json=%s WHERE id=%s",
                (text_of(soup), json.dumps(tables(soup)), page["id"]),
            )
            for child_url in menu_child_links(soup, page["source_url"]):
                child_id = imported.get(child_url)
                if child_id:
                    conn.execute("""
                        UPDATE elearn_links SET discovered_page_id=%s, link_type='child'
                        WHERE from_page_id=%s AND regexp_replace(to_url, '^http:', 'https:')=%s
                    """, (child_id, page["id"], child_url))
                    conn.execute(
                        "UPDATE elearn_pages SET parent_page_id=%s WHERE id=%s",
                        (page["id"], child_id),
                    )
                else:
                    conn.execute("""
                        UPDATE elearn_links SET link_type='child'
                        WHERE from_page_id=%s AND regexp_replace(to_url, '^http:', 'https:')=%s
                    """, (page["id"], child_url))
                    pending.append((child_url, page["id"]))
    return pending

def record_event(conn, run_id, event_type, url, message=None, parent_url=None):
    return bool(conn.execute("""
        INSERT INTO crawl_url_events(crawl_run_id,event_type,url,parent_url,message)
        VALUES(%s,%s,%s,%s,%s)
        ON CONFLICT (crawl_run_id,event_type,url) DO NOTHING
        RETURNING id
    """, (run_id, event_type, url, parent_url, message)).fetchone())

def crawl(download_images=True, resume_pending=False, limit=None):
    os.makedirs(IMG_DIR, exist_ok=True)
    pending = reconcile_existing_pages()
    effective_limit = MAX_PAGES if limit is None else max(0, limit)
    with get_conn() as conn:
        v = conn.execute("SELECT id FROM vehicles WHERE source_code='186'").fetchone() or conn.execute("INSERT INTO vehicles(make,model,source_code) VALUES('Fiat','Multipla','186') RETURNING id").fetchone()
        vehicle_id = v["id"]
        pages_before = conn.execute("SELECT count(*) n FROM elearn_pages").fetchone()["n"]
        imported_urls = {row["source_url"] for row in conn.execute("SELECT source_url FROM elearn_pages").fetchall()}
        run = conn.execute("""
            INSERT INTO crawl_runs(mode,page_limit,pages_before,pending_before)
            VALUES(%s,%s,%s,%s) RETURNING id
        """, ("resume_pending" if resume_pending else "pending_then_root", effective_limit or None, pages_before, len(pending))).fetchone()
        run_id = run["id"]
    stats = {
        "run_id": run_id, "status": "running", "pages_before": pages_before,
        "pages_after": pages_before, "pages_crawled": 0,
        "pending_before": len(pending), "pending_after": len(pending),
        "new_children_discovered": 0, "images_imported": 0,
        "failed_pages": 0, "failed_images": 0, "skipped_urls": 0,
        "failed_urls": [],
    }
    known_children = imported_urls | {url for url, _ in pending}
    seeds = list(pending)
    if not resume_pending:
        seeds.append((canonical_url(ROOT), None))
    q, seen = deque(seeds), set()
    try:
        with httpx.Client(timeout=30, headers={"User-Agent":"eLearn Phase2A research crawler (polite; contact local developer)"}, follow_redirects=True) as client:
            while q and (not effective_limit or stats["pages_crawled"] < effective_limit):
                url, parent = q.popleft()
                url = canonical_url(url)
                if url in seen:
                    with get_conn() as conn:
                        if record_event(conn, run_id, "skipped", url, "duplicate_in_run"):
                            stats["skipped_urls"] += 1
                    continue
                if not is_multipla_url(url):
                    with get_conn() as conn:
                        if record_event(conn, run_id, "skipped", url, "outside_multipla_boundary"):
                            stats["skipped_urls"] += 1
                    continue
                seen.add(url)
                try:
                    r = client.get(url); r.raise_for_status()
                    html = r.text
                except Exception as e:
                    message = str(e)
                    stats["failed_pages"] += 1
                    stats["failed_urls"].append({"type": "page", "url": url, "error": message})
                    with get_conn() as conn:
                        record_event(conn, run_id, "page_failed", url, message)
                    continue
                soup = BeautifulSoup(html, "html.parser")
                with get_conn() as conn:
                    page_url = canonical_url(str(r.url))
                    pid = upsert_page(conn, vehicle_id, page_url, html, soup, parent)
                    conn.execute("""
                        UPDATE elearn_links SET discovered_page_id=%s
                        WHERE regexp_replace(to_url, '^http:', 'https:')=%s
                    """, (pid, page_url))
                    root = content_node(soup)
                    for img in root.find_all("img"):
                        src = img.get("src")
                        if not src: continue
                        iu = canonical_url(urljoin(page_url, src))
                        if not is_multipla_image(iu):
                            if record_event(conn, run_id, "skipped", iu, "non_multipla_image", page_url):
                                stats["skipped_urls"] += 1
                            continue
                        local = None
                        if download_images:
                            ext = os.path.splitext(urlparse(iu).path)[1] or ".img"
                            fn = hashlib.sha1(iu.encode()).hexdigest()+ext
                            storage_path = os.path.join(IMG_DIR, fn)
                            local = f"{PUBLIC_IMAGE_PATH.rstrip('/')}/{fn}"
                            if not os.path.exists(storage_path):
                                try:
                                    ir = client.get(iu); ir.raise_for_status()
                                    with open(storage_path,"wb") as image_file:
                                        image_file.write(ir.content)
                                    stats["images_imported"] += 1
                                except Exception as e:
                                    message = str(e)
                                    local = None
                                    stats["failed_images"] += 1
                                    stats["failed_urls"].append({"type": "image", "url": iu, "error": message})
                                    record_event(conn, run_id, "image_failed", iu, message, page_url)
                        conn.execute("""
                            INSERT INTO elearn_images(elearn_page_id,image_url,local_path,alt_text)
                            VALUES(%s,%s,%s,%s)
                            ON CONFLICT (elearn_page_id, image_url) DO UPDATE
                            SET local_path=COALESCE(EXCLUDED.local_path, elearn_images.local_path),
                                alt_text=COALESCE(EXCLUDED.alt_text, elearn_images.alt_text)
                        """, (pid, iu, local, img.get("alt")))
                    priority_urls = menu_child_links(soup, page_url)
                    for child_url in priority_urls:
                        if child_url not in known_children:
                            known_children.add(child_url)
                            stats["new_children_discovered"] += 1
                    regular_urls = []
                    for a in soup.find_all("a", href=True):
                        to = canonical_url(urljoin(page_url, a["href"]))
                        txt = a.get_text(" ", strip=True)
                        child = conn.execute("SELECT id FROM elearn_pages WHERE source_url=%s", (to,)).fetchone()
                        child_id = child["id"] if child else None
                        conn.execute("""
                            INSERT INTO elearn_links(from_page_id,to_url,link_text,discovered_page_id,link_type)
                            VALUES(%s,%s,%s,%s,%s)
                            ON CONFLICT (from_page_id,to_url) DO UPDATE
                            SET link_text=EXCLUDED.link_text,
                                discovered_page_id=COALESCE(EXCLUDED.discovered_page_id, elearn_links.discovered_page_id),
                                link_type=CASE WHEN EXCLUDED.link_type='child' THEN 'child' ELSE COALESCE(elearn_links.link_type, EXCLUDED.link_type) END
                        """, (pid, to, txt, child_id, "child" if to in priority_urls else "navigation"))
                        if child_id:
                            conn.execute("""
                                UPDATE elearn_links SET discovered_page_id=%s
                                WHERE from_page_id=%s AND regexp_replace(to_url, '^http:', 'https:')=%s
                            """, (child_id, pid, to))
                            if to in priority_urls:
                                conn.execute("UPDATE elearn_pages SET parent_page_id=%s WHERE id=%s", (pid, child_id))
                        if is_multipla_url(to):
                            if to not in seen and to not in priority_urls:
                                regular_urls.append(to)
                        elif record_event(conn, run_id, "skipped", to, "outside_multipla_boundary", page_url):
                            stats["skipped_urls"] += 1
                    q.extendleft((to, pid) for to in reversed(priority_urls) if to not in seen)
                    q.extend((to, None) for to in regular_urls)
                stats["pages_crawled"] += 1
                print(f"crawled {stats['pages_crawled']}: {url}")
                time.sleep(RATE)
        pending_after = reconcile_existing_pages()
        with get_conn() as conn:
            stats["pages_after"] = conn.execute("SELECT count(*) n FROM elearn_pages").fetchone()["n"]
            stats["pending_after"] = len(pending_after)
            stats["status"] = "complete" if not pending_after else ("limited" if effective_limit and stats["pages_crawled"] >= effective_limit else "partial")
            conn.execute("""
                UPDATE crawl_runs SET status=%s,pages_after=%s,pending_after=%s,pages_crawled=%s,
                  new_children_discovered=%s,images_imported=%s,failed_pages=%s,failed_images=%s,
                  skipped_urls=%s,finished_at=now() WHERE id=%s
            """, (stats["status"], stats["pages_after"], stats["pending_after"], stats["pages_crawled"],
                  stats["new_children_discovered"], stats["images_imported"], stats["failed_pages"],
                  stats["failed_images"], stats["skipped_urls"], run_id))
        return stats
    except BaseException as e:
        with get_conn() as conn:
            conn.execute("""
                UPDATE crawl_runs SET status='failed',pages_crawled=%s,new_children_discovered=%s,
                  images_imported=%s,failed_pages=%s,failed_images=%s,skipped_urls=%s,error=%s,
                  finished_at=now() WHERE id=%s
            """, (stats["pages_crawled"], stats["new_children_discovered"], stats["images_imported"],
                  stats["failed_pages"], stats["failed_images"], stats["skipped_urls"], str(e), run_id))
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl Fiat Multipla eLearn pages")
    parser.add_argument("--resume-pending", action="store_true", help="crawl known unresolved child URLs without restarting at the root")
    parser.add_argument("--limit", type=int, default=None, help="maximum successfully fetched pages for this run; 0 means unlimited")
    parser.add_argument("--no-images", action="store_true", help="do not download article images")
    options = parser.parse_args()
    print(crawl(download_images=not options.no_images, resume_pending=options.resume_pending, limit=options.limit))
