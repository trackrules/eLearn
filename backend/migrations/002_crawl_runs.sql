CREATE TABLE IF NOT EXISTS crawl_runs (
  id BIGSERIAL PRIMARY KEY,
  mode TEXT NOT NULL,
  page_limit INTEGER,
  status TEXT NOT NULL DEFAULT 'running',
  pages_before INTEGER NOT NULL DEFAULT 0,
  pages_after INTEGER,
  pending_before INTEGER NOT NULL DEFAULT 0,
  pending_after INTEGER,
  pages_crawled INTEGER NOT NULL DEFAULT 0,
  new_children_discovered INTEGER NOT NULL DEFAULT 0,
  images_imported INTEGER NOT NULL DEFAULT 0,
  failed_pages INTEGER NOT NULL DEFAULT 0,
  failed_images INTEGER NOT NULL DEFAULT 0,
  skipped_urls INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS crawl_url_events (
  id BIGSERIAL PRIMARY KEY,
  crawl_run_id BIGINT NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  url TEXT NOT NULL,
  parent_url TEXT,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(crawl_run_id, event_type, url)
);

CREATE INDEX IF NOT EXISTS crawl_url_events_type_idx
  ON crawl_url_events(event_type, created_at DESC);
