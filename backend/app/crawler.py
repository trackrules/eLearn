import hashlib, json, os, re, time
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from .db import get_conn

ROOT = "https://4cardata.info/elearn/186/2/"
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

def crawl(download_images=True):
    os.makedirs(IMG_DIR, exist_ok=True)
    stats = {"pages": 0, "images": 0, "failed_urls": []}
    with get_conn() as conn:
        v = conn.execute("SELECT id FROM vehicles WHERE source_code='186'").fetchone() or conn.execute("INSERT INTO vehicles(make,model,source_code) VALUES('Fiat','Multipla','186') RETURNING id").fetchone()
        vehicle_id = v["id"]
    q, seen = deque([(canonical_url(ROOT), None)]), set()
    with httpx.Client(timeout=30, headers={"User-Agent":"eLearn Phase2A research crawler (polite; contact local developer)"}, follow_redirects=True) as client:
        while q and (not MAX_PAGES or stats["pages"] < MAX_PAGES):
            url, parent = q.popleft()
            url = canonical_url(url)
            if url in seen or not is_multipla_url(url): continue
            seen.add(url)
            try:
                r = client.get(url); r.raise_for_status()
                html = r.text
            except Exception as e:
                stats["failed_urls"].append({"url": url, "error": str(e)}); continue
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
                    iu = urljoin(str(r.url), src)
                    if not is_multipla_image(iu): continue
                    local = None
                    if download_images:
                        ext = os.path.splitext(urlparse(iu).path)[1] or ".img"
                        fn = hashlib.sha1(iu.encode()).hexdigest()+ext
                        storage_path = os.path.join(IMG_DIR, fn)
                        local = f"{PUBLIC_IMAGE_PATH.rstrip('/')}/{fn}"
                        if not os.path.exists(storage_path):
                            try:
                                ir = client.get(iu); ir.raise_for_status(); open(storage_path,"wb").write(ir.content); stats["images"] += 1
                            except Exception as e: stats["failed_urls"].append({"url": iu, "error": str(e)})
                    conn.execute("""
                        INSERT INTO elearn_images(elearn_page_id,image_url,local_path,alt_text)
                        VALUES(%s,%s,%s,%s)
                        ON CONFLICT (elearn_page_id, image_url) DO UPDATE
                        SET local_path=COALESCE(EXCLUDED.local_path, elearn_images.local_path),
                            alt_text=COALESCE(EXCLUDED.alt_text, elearn_images.alt_text)
                    """, (pid, iu, local, img.get("alt")))
                priority_urls = menu_child_links(soup, page_url)
                regular_urls = []
                for a in soup.find_all("a", href=True):
                    to = canonical_url(urljoin(page_url, a["href"]))
                    txt = a.get_text(" ", strip=True)
                    child = conn.execute("SELECT id FROM elearn_pages WHERE source_url=%s", (to,)).fetchone()
                    child_id = child["id"] if child else None
                    conn.execute("""
                        INSERT INTO elearn_links(from_page_id,to_url,link_text,discovered_page_id)
                        VALUES(%s,%s,%s,%s)
                        ON CONFLICT (from_page_id,to_url) DO UPDATE
                        SET link_text=EXCLUDED.link_text,
                            discovered_page_id=COALESCE(EXCLUDED.discovered_page_id, elearn_links.discovered_page_id)
                    """, (pid, to, txt, child_id))
                    if child_id:
                        conn.execute("""
                            UPDATE elearn_links SET discovered_page_id=%s
                            WHERE from_page_id=%s AND regexp_replace(to_url, '^http:', 'https:')=%s
                        """, (child_id, pid, to))
                        if to in priority_urls:
                            conn.execute("UPDATE elearn_pages SET parent_page_id=%s WHERE id=%s", (pid, child_id))
                    if is_multipla_url(to) and to not in seen and to not in priority_urls:
                        regular_urls.append(to)
                q.extendleft((to, pid) for to in reversed(priority_urls) if to not in seen)
                q.extend((to, None) for to in regular_urls)
            stats["pages"] += 1
            print(f"crawled {stats['pages']}: {url}")
            time.sleep(RATE)
    return stats

if __name__ == "__main__":
    print(crawl())
