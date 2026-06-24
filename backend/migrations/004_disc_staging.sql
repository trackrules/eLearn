CREATE SCHEMA IF NOT EXISTS disc_staging;

CREATE TABLE IF NOT EXISTS disc_staging.source_release (
  id BIGSERIAL PRIMARY KEY,
  release_key TEXT NOT NULL UNIQUE,
  source_name TEXT NOT NULL,
  model_code TEXT NOT NULL,
  language_id INTEGER NOT NULL,
  source_database_path TEXT NOT NULL,
  source_database_sha256 CHAR(64) NOT NULL CHECK (source_database_sha256 ~ '^[0-9A-F]{64}$'),
  source_asset_path TEXT NOT NULL,
  importer_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('importing', 'complete', 'failed')),
  counts JSONB NOT NULL DEFAULT '{}'::jsonb,
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_language (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_language_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  set_code TEXT,
  internal_search BOOLEAN,
  PRIMARY KEY (release_id, source_language_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_model (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_model_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  source_mark_id BIGINT,
  name TEXT NOT NULL,
  code TEXT NOT NULL,
  PRIMARY KEY (release_id, source_model_id, source_language_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_section (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_section_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  source_model_id BIGINT NOT NULL,
  root_element_id BIGINT,
  name TEXT NOT NULL,
  section_type INTEGER NOT NULL,
  orders INTEGER,
  clickable BOOLEAN,
  indent INTEGER,
  PRIMARY KEY (release_id, source_section_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_element (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_element_id BIGINT NOT NULL,
  source_section_id BIGINT NOT NULL,
  parent_element_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  orders INTEGER,
  all_codep BOOLEAN NOT NULL,
  all_validity BOOLEAN NOT NULL,
  all_production BOOLEAN NOT NULL,
  layout INTEGER,
  breadcrumb JSONB NOT NULL DEFAULT '[]'::jsonb,
  PRIMARY KEY (release_id, source_element_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_xml (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_xml_id BIGINT NOT NULL,
  source_element_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  raw_xml TEXT NOT NULL,
  raw_xml_sha256 CHAR(64) NOT NULL CHECK (raw_xml_sha256 ~ '^[0-9a-f]{64}$'),
  full_text TEXT,
  normalized_text TEXT NOT NULL,
  normalized_text_sha256 CHAR(64) NOT NULL CHECK (normalized_text_sha256 ~ '^[0-9a-f]{64}$'),
  orders INTEGER,
  all_codep BOOLEAN NOT NULL,
  all_validity BOOLEAN NOT NULL,
  all_production BOOLEAN NOT NULL,
  PRIMARY KEY (release_id, source_xml_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_production (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_production_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  source_model_id BIGINT NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  validity_id BIGINT,
  PRIMARY KEY (release_id, source_production_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_validity (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_validity_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  source_model_id BIGINT NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  orders INTEGER,
  PRIMARY KEY (release_id, source_validity_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_codep (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_codep_id BIGINT NOT NULL,
  source_language_id INTEGER NOT NULL,
  source_model_id BIGINT NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  PRIMARY KEY (release_id, source_codep_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_element_applicability (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_element_id BIGINT NOT NULL,
  applicability_type TEXT NOT NULL CHECK (applicability_type IN ('production', 'validity', 'codep')),
  applicability_id BIGINT NOT NULL,
  PRIMARY KEY (release_id, source_element_id, applicability_type, applicability_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_xml_applicability (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_xml_id BIGINT NOT NULL,
  applicability_type TEXT NOT NULL CHECK (applicability_type IN ('production', 'validity', 'codep')),
  applicability_id BIGINT NOT NULL,
  PRIMARY KEY (release_id, source_xml_id, applicability_type, applicability_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_content_link (
  id BIGSERIAL PRIMARY KEY,
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_xml_id BIGINT NOT NULL,
  ordinal INTEGER NOT NULL,
  target_id BIGINT NOT NULL,
  target_code TEXT,
  target_description TEXT,
  link_kind TEXT NOT NULL CHECK (link_kind IN ('resolved_element', 'local_anchor', 'unresolved_target')),
  UNIQUE (release_id, source_xml_id, ordinal)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_asset (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_asset_id TEXT NOT NULL,
  source_path TEXT NOT NULL,
  exists_on_disc BOOLEAN NOT NULL,
  byte_size BIGINT,
  byte_sha256 CHAR(64),
  detected_type TEXT NOT NULL CHECK (detected_type IN ('JPEG', 'SVG', 'gzipped SVG', 'unknown')),
  PRIMARY KEY (release_id, source_asset_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_content_asset (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  source_xml_id BIGINT NOT NULL,
  ordinal INTEGER NOT NULL,
  source_asset_id TEXT NOT NULL,
  reference_kind TEXT NOT NULL CHECK (reference_kind IN ('imageid', 'conimageid')),
  PRIMARY KEY (release_id, source_xml_id, ordinal)
);

CREATE TABLE IF NOT EXISTS disc_staging.disc_exception (
  id BIGSERIAL PRIMARY KEY,
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  exception_type TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  resolution_status TEXT NOT NULL DEFAULT 'open' CHECK (resolution_status IN ('open', 'accepted', 'resolved')),
  UNIQUE (release_id, exception_type, subject_type, subject_id)
);

CREATE TABLE IF NOT EXISTS disc_staging.web_disc_match (
  release_id BIGINT NOT NULL REFERENCES disc_staging.source_release(id) ON DELETE CASCADE,
  web_page_id BIGINT NOT NULL,
  source_element_id BIGINT,
  source_xml_id BIGINT,
  match_method TEXT NOT NULL,
  match_score NUMERIC(7,6),
  classification TEXT NOT NULL,
  source_url TEXT,
  PRIMARY KEY (release_id, web_page_id)
);

CREATE INDEX IF NOT EXISTS idx_disc_element_parent ON disc_staging.disc_element(release_id, parent_element_id);
CREATE INDEX IF NOT EXISTS idx_disc_xml_element ON disc_staging.disc_xml(release_id, source_element_id);
CREATE INDEX IF NOT EXISTS idx_disc_xml_hash ON disc_staging.disc_xml(release_id, normalized_text_sha256);
CREATE INDEX IF NOT EXISTS idx_disc_link_target ON disc_staging.disc_content_link(release_id, target_id);
CREATE INDEX IF NOT EXISTS idx_disc_exception_type ON disc_staging.disc_exception(release_id, exception_type);
