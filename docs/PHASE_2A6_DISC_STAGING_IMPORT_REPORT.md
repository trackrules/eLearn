# Phase 2A.6 Disc Staging Import Report

## Outcome

The English Fiat Multipla disc was imported into the isolated `disc_staging` schema. Production tables were not changed or replaced. Release `multipla-186-en-3b9babeb029a` completed with source database SHA-256 `3B9BABEB029ABF75F469A17BD9A7735EFC50F7751EDE7484CC6BCBCC7D385394` after a byte-identical temporary copy was opened through ACE in read-only mode.

## Imported counts

| Table | Rows |
|---|---:|
| `disc_language` | 1 |
| `disc_model` | 1 |
| `disc_section` | 6 |
| `disc_element` | 5,111 |
| `disc_xml` | 7,177 |
| `disc_production` | 6 |
| `disc_validity` | 2 |
| `disc_codep` | 21 |
| `disc_element_applicability` | 10,144 |
| `disc_xml_applicability` | 13,603 |
| `disc_content_link` | 54,169 |
| `disc_asset` | 4,140 |
| `disc_content_asset` | 13,265 |
| `disc_exception` | 8,140 |
| `web_disc_match` | 6,949 |

The core counts match Phase 2A.5: 5,111 elements, 7,177 XML records, 4,064 physical native assets, 3,959 English-referenced asset IDs, and 76 referenced-but-missing English assets. `disc_asset` therefore contains 4,140 rows: every physical asset plus missing-reference placeholders.

## Persisted exceptions

| Exception type | Rows |
|---|---:|
| `disc_only_xml_variant` | 3,955 |
| `local_anchor` | 2,059 |
| `missing_asset` | 76 |
| `unresolved_comparison` | 433 |
| `unresolved_target` | 347 |
| `web_only_wrapper` | 2 |
| `web_richer` | 1,268 |

Every XML row preserves the source XML ID, element ID, raw XML, raw XML SHA-256, normalized text and normalized-text SHA-256. Assets preserve source IDs, paths, existence, detected type and byte SHA-256 where present. Applicability remains separated at element and XML scope.

Post-load integrity validation found 0 XML/text hash mismatches and 0 unhashed physical assets. The physical corpus is {'JPEG': 3247, 'SVG': 5, 'gzipped SVG': 812} and `disc_content_asset` references 3,959 distinct source asset IDs.

No production page, image, link, component, or search-index record was replaced.
