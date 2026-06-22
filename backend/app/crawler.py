import hashlib, json, os, re, time
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from .db import get_conn

ROOT = "https://4cardata.info/elearn/186/"
RATE = float(os.getenv("CRAWL_RATE_SECONDS", "1.0"))
IMG_DIR = os.getenv("IMAGE_STORAGE_DIR", "storage/images")
MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "0"))


def is_multipla_url(url):
    p = urlparse(url)
    return p.netloc == "4cardata.info" and "/elearn/186" in p.path

def source_id(url):
    qs = parse_qs(urlparse(url).query)
    return qs.get("id", [None])[0] or os.path.basename(urlparse(url).path) or None

def text_of(soup):
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

def tables(soup):
    out = []
    for table in soup.find_all("table"):
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
    q, seen = deque([(ROOT, None)]), set()
    with httpx.Client(timeout=30, headers={"User-Agent":"eLearn Phase2A research crawler (polite; contact local developer)"}, follow_redirects=True) as client:
        while q and (not MAX_PAGES or stats["pages"] < MAX_PAGES):
            url, parent = q.popleft()
            if url in seen or not is_multipla_url(url): continue
            seen.add(url)
            try:
                r = client.get(url); r.raise_for_status()
                html = r.text
            except Exception as e:
                stats["failed_urls"].append({"url": url, "error": str(e)}); continue
            soup = BeautifulSoup(html, "html.parser")
            with get_conn() as conn:
                pid = upsert_page(conn, vehicle_id, str(r.url), html, soup, parent)
                for img in soup.find_all("img"):
                    src = img.get("src")
                    if not src: continue
                    iu = urljoin(str(r.url), src)
                    local = None
                    if download_images and (is_multipla_url(iu) or "/elearn/186" in urlparse(iu).path):
                        ext = os.path.splitext(urlparse(iu).path)[1] or ".img"
                        fn = hashlib.sha1(iu.encode()).hexdigest()+ext
                        local = os.path.join(IMG_DIR, fn)
                        if not os.path.exists(local):
                            try:
                                ir = client.get(iu); ir.raise_for_status(); open(local,"wb").write(ir.content); stats["images"] += 1
                            except Exception as e: stats["failed_urls"].append({"url": iu, "error": str(e)})
                    conn.execute("INSERT INTO elearn_images(elearn_page_id,image_url,local_path,alt_text) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING", (pid, iu, local, img.get("alt")))
                for a in soup.find_all("a", href=True):
                    to = urljoin(str(r.url), a["href"]).split("#",1)[0]
                    txt = a.get_text(" ", strip=True)
                    conn.execute("INSERT INTO elearn_links(from_page_id,to_url,link_text) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING", (pid, to, txt))
                    if is_multipla_url(to) and to not in seen: q.append((to, pid))
            stats["pages"] += 1
            print(f"crawled {stats['pages']}: {url}")
            time.sleep(RATE)
    return stats

if __name__ == "__main__":
    print(crawl())
