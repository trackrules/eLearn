# eLearn Import Recommendation

## Recommendation

Choose **C: a hybrid approach**, with the mounted disc becoming the authoritative structured source for future extraction work and the existing web crawl retained as a rendered-content baseline, validation corpus, and gap fallback.

Do not immediately replace the current 6,951-page production dataset. Do not import yet. Do not start Phase 2B.

## Decision summary

| Option | Decision | Reason |
|---|---|---|
| A. Keep web crawl as primary | Reject for future source development | It discards explicit applicability, native XML, navigation IDs, cross-links, multilingual content, and original SVG/component identity |
| B. Replace web source immediately | Reject now | Exact page/asset parity is unmeasured; the disc has 91 missing asset references, unresolved links, and no online update package |
| C. Hybrid, disc-first staging | **Recommend** | Gains canonical structure and native assets while preserving the proven web corpus for comparison and fallback |

## Why the disc should drive future development

The English disc database contains 7,177 raw XML records versus the current 6,951-page baseline, a potential surplus of 226 records. More importantly, it preserves information that rendered web pages flatten or lose:

- 5,111 ordered navigation nodes and six roots;
- 54,169 English cross-link target occurrences;
- six production ranges;
- two engine/version validities;
- 21 equipment/option dimensions;
- 2,232 element-level and 2,913 XML-level English option associations;
- 8,229 element-level and 12,161 XML-level English production associations;
- 4,422 element-level and 6,256 XML-level English validity associations;
- 2,634 English wiring XML records;
- original native SVG wiring/component diagrams;
- component, assembly, connector, procedure, diagnostic, and image IDs;
- eight technical languages.

This makes the disc the better source for search, filtering, applicability, cross-linking, component identity, diagram handling, and future domain modeling.

## Why not replace the web crawl immediately

The two datasets have not yet been compared at record level. The supplied platform counts are aggregates only:

| Platform metric | Disc comparison issue |
|---|---|
| 6,951 pages | A page may represent one element, one XML variant, or a rendered applicability combination; it cannot be equated blindly with 7,177 XML rows |
| 10,552 images | The disc has 4,064 native assets; the web count may include repeated downloads, thumbnails, rasterized SVG, UI images, or crawl variants |
| 1,064 component matches | The disc has 640 unique English wiring target IDs and 806 structured wiring codes, but the semantics of a platform “match” differ |

Known disc gaps also require handling:

- 91 referenced image/component asset IDs are absent;
- 347 English non-anchor target occurrences do not resolve to an English element;
- Polish has eight orphan parent rows;
- no update database is present;
- Czech, Greek, and Turkish technical databases are absent;
- the disc dates from 2004 and may predate later web corrections.

The current web import should remain untouched until these differences are classified.

## Proposed source-of-truth split

| Data class | Primary source | Secondary/fallback |
|---|---|---|
| Model, section, node hierarchy | Disc | Web URL/title structure for validation |
| Raw technical content | Disc XML after safe transformation | Existing rendered web HTML for parity and gap fill |
| Production/validity/equipment applicability | Disc | None unless independently verified |
| Cross-links and component identities | Disc target/code fields | Existing component matches as reconciliation evidence |
| Native JPEG/SVG assets | Disc | Web images for missing IDs, later revisions, and rendered derivatives |
| User-facing rendered output | New safe renderer | Existing web page as regression oracle |
| Multilingual content | Disc | Web where available |
| Provenance | Preserve both | Never overwrite one source's identity with the other |

## Required Phase 2A continuation

The next step should remain Phase 2A: build a **read-only comparison manifest**, not an importer.

### 1. Freeze source identities

- Record the eight database hashes already documented.
- Hash all 4,064 native assets.
- Record the current platform export/version and crawl timestamp.
- Treat `(database SHA-256, language ID, source table, source ID)` as immutable provenance.

### 2. Obtain a current-platform comparison export

Export read-only fields sufficient for matching:

- platform page ID and canonical URL;
- original `nodeID`, `modelID`, `languageID`, `prodID`, and `valID` where available;
- title, procedure/wiring/diagnostic code, normalized text hash;
- image source URL, filename, dimensions, byte hash, and page association;
- component-match source and confidence.

Without this export, no reliable “new versus duplicate” classification is possible.

### 3. Build a disc manifest in isolated staging

Read each Jet database directly from a temporary working copy. Produce immutable manifest rows for:

- model/language/section;
- elements and their parents/order;
- XML variants and `ALL_*` flags;
- production, validity, and CODEP associations;
- target IDs and structured codes;
- image/conimage IDs and physical file hashes;
- exceptions: missing assets, orphan parents, and unresolved targets.

Do not repair or relink the source databases.

### 4. Compare using multiple keys

Use a match hierarchy:

1. exact source IDs recovered from web URLs/query strings;
2. model + language + element/procedure/wiring code;
3. normalized title + normalized text hash;
4. image byte hash or SVG canonical hash;
5. manual review for ambiguous records.

Classify each record as:

- exact duplicate;
- same content with richer disc metadata;
- web-only/later revision;
- disc-only candidate;
- asset-only addition;
- conflicting version;
- unresolved.

### 5. Validate rendering safely

- Parse XML with DTD/external entity and network/file resolution disabled.
- Apply only audited XSLT 1.0 behavior.
- Disable script, ActiveX, VBScript, extension functions, and external resource loading.
- Sanitize SVG and retain original bytes separately.
- Rewrite `targetid` links to stable internal staging IDs.
- Compare rendered text, headings, tables, images, and links against representative existing web pages.

### 6. Set promotion gates before Phase 2B

Do not authorize an import until a review confirms:

- page/content match rate;
- number and samples of disc-only records;
- exact asset deduplication results;
- applicability preservation tests;
- link-resolution rate and exception policy;
- rendered regression samples for all six section types;
- rollback and provenance behavior;
- no writes to the production database during dry runs.

## Proposed target data model

The production design should preserve source semantics rather than flatten immediately:

```text
source_release
vehicle_model
language
section
element (parent_element_id, order, code)
content_variant (raw_xml, normalized_text, order)
production_range
validity
equipment_option
element_applicability
content_applicability
content_link (source_target_id, resolved_element_id, link_code)
asset (source_image_id, detected_type, hash, original_bytes_path)
content_asset
source_exception
web_disc_match
```

Existing user-facing page records can remain as a presentation/search layer derived from these source entities.

## Risk controls

- Never open the original optical-media Jet files through a provider that may create lock/repair data; use verified temporary copies.
- Never change linked-table definitions in `C:\eLearn\Database\eLearnHD.dat`.
- Never use the legacy launcher/viewer to perform extraction.
- Preserve raw XML/SVG bytes before normalization.
- Keep source-local IDs scoped by database/language because translated IDs differ.
- Treat targets 0 and 1 with `ref='page'` as local anchors, not broken node links.
- Treat `CODEP` as equipment applicability, not diagnostic fault codes.
- Do not infer a missing asset from extension alone; use IDs and byte signatures.
- Keep web-only and disc-only provenance visible to users and maintainers.

## Answers to the four final questions

### 1. Does Multipla content exist?

**Yes.** Actual records identify Fiat `MULTIPLA`, model ID `2000006`, model code `186`, in eight language databases.

### 2. Is the disc richer than the web crawl?

**Yes, structurally and semantically.** It includes raw XML, ordered hierarchy, applicability, native SVG/JPEG assets, cross-links, component codes, and multilingual records. It also has 7,177 English XML records versus the 6,951-page crawl baseline, although an exact overlap/delta requires record-level matching.

### 3. Is it worth switching future development to the disc source?

**Yes, for source extraction and domain modeling.** It should become the canonical structured source in staging. Do not switch production wholesale until parity and exception analysis is complete.

### 4. Recommended next step

Perform a read-only Phase 2A manifest comparison between `elearn_2.dat` plus the native assets and an export of the current 6,951 pages, 10,552 images, and 1,064 component matches. Produce a reviewed diff and dry-run proposal. Do not import and do not begin Phase 2B yet.
