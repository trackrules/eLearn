ALTER TABLE elearn_links ADD COLUMN IF NOT EXISTS link_type TEXT;

CREATE INDEX IF NOT EXISTS elearn_links_child_type_idx
  ON elearn_links(from_page_id, link_type, discovered_page_id);
