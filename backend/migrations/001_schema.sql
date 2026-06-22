CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS vehicles (
  id BIGSERIAL PRIMARY KEY,
  make TEXT NOT NULL,
  model TEXT NOT NULL,
  source_code TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS elearn_pages (
  id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  source_url TEXT NOT NULL UNIQUE,
  source_id TEXT,
  title TEXT NOT NULL,
  breadcrumb TEXT,
  category TEXT,
  raw_html TEXT NOT NULL,
  content_text TEXT,
  tables_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  parent_page_id BIGINT REFERENCES elearn_pages(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS elearn_images (
  id BIGSERIAL PRIMARY KEY,
  elearn_page_id BIGINT NOT NULL REFERENCES elearn_pages(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  local_path TEXT,
  alt_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(elearn_page_id, image_url)
);

CREATE TABLE IF NOT EXISTS elearn_links (
  id BIGSERIAL PRIMARY KEY,
  from_page_id BIGINT NOT NULL REFERENCES elearn_pages(id) ON DELETE CASCADE,
  to_url TEXT NOT NULL,
  link_text TEXT,
  discovered_page_id BIGINT REFERENCES elearn_pages(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(from_page_id, to_url)
);

CREATE TABLE IF NOT EXISTS components (
  id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(vehicle_id, slug)
);

CREATE TABLE IF NOT EXISTS component_aliases (
  id BIGSERIAL PRIMARY KEY,
  component_id BIGINT NOT NULL REFERENCES components(id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  UNIQUE(component_id, alias)
);

CREATE TABLE IF NOT EXISTS component_page_links (
  id BIGSERIAL PRIMARY KEY,
  component_id BIGINT NOT NULL REFERENCES components(id) ON DELETE CASCADE,
  elearn_page_id BIGINT NOT NULL REFERENCES elearn_pages(id) ON DELETE CASCADE,
  match_type TEXT NOT NULL,
  match_score NUMERIC NOT NULL,
  matched_text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(component_id, elearn_page_id, matched_text)
);

INSERT INTO vehicles(make, model, source_code)
VALUES ('Fiat', 'Multipla', '186')
ON CONFLICT (source_code) DO NOTHING;
