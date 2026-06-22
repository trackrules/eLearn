# Phase 2A Multipla crawler-quality report

Audit date: 2026-06-22

Scope: Fiat Multipla eLearn code `186` only. No Phase 2B capabilities were added.

## Final coverage

| Metric | Count |
|---|---:|
| Imported pages | 6,951 |
| Engine 1.6 16V pages | 3,605 |
| Engine 1.9 JTD 8V pages | 3,344 |
| Root/navigation pages | 2 |
| Pages with hierarchy children | 1,554 |
| Resolved menu-child parent pages | 1,553 |
| Resolved menu-child edges | 7,147 |
| Leaf/article pages | 5,397 |
| Pages with image references | 4,265 |
| Pages with locally downloaded images | 4,251 |
| Image records | 10,626 |
| Local image records | 10,552 |
| Known unimported child URLs | **0** |
| Search documents indexed | **6,951** |
| Component-page matches | 1,064 |

## Engine and section coverage

| Engine variant | Pages |
|---|---:|
| 1.6 16V | 3,605 |
| 1.9 JTD 8V | 3,344 |
| Root/navigation | 2 |

| Top-level section | Pages |
|---|---:|
| ELECTRICAL EQUIPMENT | 3,441 |
| PROCEDURES | 2,257 |
| TECHNICAL DATA | 496 |
| FAULT DIAGNOSIS | 385 |
| DESCRIPTIONS | 261 |
| TEST | 107 |
| Root/navigation | 4 |

## Categories

| Category | Pages | Category | Pages |
|---|---:|---|---:|
| 3 CONNECTORS | 2,690 | 70 FITTINGS | 682 |
| 1 ELECTRICAL FUNCTIONS | 669 | 10 ENGINE UNIT | 630 |
| 55 ELECTRICAL EQUIPMENT | 352 | 50 AUXILIARY UNITS | 262 |
| 33 BRAKING SYSTEM | 228 | MANUFACTURING DATA | 146 |
| PROJECT DESCRIPTION AND SPECIFICATIONS | 134 | TIGHTENING TORQUES | 130 |
| 44 SUSPENSION AND WHEELS | 122 | 2 WIRING | 80 |
| 41 STEERING | 71 | 72 PANELS AND FRAME | 64 |
| 21 GEARBOX | 59 | 00 MAINTENANCE | 58 |
| S NOISY' / VIBRATIONS | 52 | 18 CLUTCH | 46 |
| K INSTRUMENT PANEL | 44 | PRODUCTS | 34 |
| D ENGINE | 28 | GENERAL INFORMATION | 26 |
| L CLIMATE CONTROL | 26 | 27 AXLE | 24 |
| I LIGHTS | 24 | SPECIAL TOOLS | 24 |
| 05 DIAGNOSTICS | 21 | J WINDSCREEN /REARSCREEN /REAR VIEW MIRRORS (VISIBILITY) | 20 |
| X CONSUMPTION /LEAKS/ WEAR | 20 | B STARTING | 19 |
| Root/navigation | 16 | H STEERING (VEHICLE BEHAVIOUR) | 16 |
| N RADIO AND ACCESSORIES ETC.. | 16 | A ALARM | 14 |
| F BRAKING SYSTEM | 14 | T WIND NOISE | 14 |
| W EMISSIONS | 12 | E CLUTCH | 10 |
| M WINDOW OPENING MECHANISM | 10 | P DOORS | 10 |
| U ODOURS | 10 | V WATER PENETRATION | 10 |
| C GEAR SHIFT | 8 | G HANDBRAKE | 6 |

## Completion-run ledger

Every crawl run is persisted in `crawl_runs`; URL-level failures and skips are persisted in `crawl_url_events`.

| Run | Limit | Pages before→after | Pending before→after | Fetched | New children | Images | Page failures | Image failures | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 2 | 1,155→1,157 | 1,478→1,476 | 2 | 0 | 2 | 0 | 0 | limited |
| 2 | 500 | 1,157→1,657 | 1,476→1,313 | 500 | 337 | 839 | 0 | 0 | limited |
| 3 | 500 | 1,657→2,157 | 1,313→1,215 | 500 | 402 | 561 | 0 | 23 | limited |
| 4 | 500 | 2,157→2,657 | 1,215→1,126 | 500 | 411 | 525 | 0 | 7 | limited |
| 5 | 500 | 2,657→3,157 | 1,126→1,043 | 500 | 417 | 75 | 0 | 0 | limited |
| 6 | 500 | 3,157→3,657 | 1,043→912 | 500 | 369 | 48 | 0 | 6 | limited |
| 7 | 500 | 3,657→4,157 | 912→755 | 500 | 343 | 77 | 0 | 2 | limited |
| 8 | 500 | 4,157→4,657 | 755→552 | 500 | 297 | 445 | 0 | 0 | limited |
| 9 | 500 | 4,657→5,157 | 552→463 | 500 | 411 | 43 | 0 | 22 | limited |
| 10 | 500 | 5,157→5,657 | 463→388 | 500 | 425 | 16 | 0 | 7 | limited |
| 11 | 500 | 5,657→6,157 | 388→291 | 500 | 403 | 1 | 0 | 2 | limited |
| 12 | 500 | 6,157→6,657 | 291→146 | 500 | 355 | 15 | 0 | 2 | limited |
| 13 | 500 | 6,657→6,951 | 146→0 | 500 | 148 | 1 | 0 | 3 | complete |
| 14 | 500 | 6,951→6,951 | 0→0 | 0 | 0 | 0 | 0 | 0 | complete/no-op |

Totals: 6,002 successful fetches, 5,796 new unique pages, 4,318 children discovered during completion, and 2,648 newly downloaded images.

## Resumability and persistence changes

The crawler now supports:

```bash
python -m app.crawler --resume-pending --limit 500
```

Each bounded run:

- starts from unresolved stored menu children rather than the root;
- reparses stored raw HTML and reconciles links before starting;
- adds newly discovered menu children to the active queue;
- persists run status and before/after metrics;
- persists failed page URLs, failed image URLs, and skipped URLs;
- can be restarted safely from the remaining stored child set;
- reports pages, pending children, new children, images, failures, and skips.

Explicit `child` link types preserve shared parent→child relationships that cannot be represented by a single `parent_page_id` value.

## Failed and skipped URLs

- Page failures: **0**.
- Persisted image-failure events: 69 events covering 36 unique source URLs.
- Image records without a local file: 74.
- All observed image failures were real source HTTP 404 responses.
- Persisted skipped events: 52 events covering four unique out-of-scope site/navigation URLs.
- Unresolved child edges: **0**.

The detailed URL, parent URL, error/reason, run ID, and timestamp are retained in `crawl_url_events`.

## Final quality audit

| Heuristic | Count | Assessment |
|---|---:|---|
| `content_text` shorter than 100 characters | 990 | Mostly index labels and image-led wiring pages; length alone is not an extraction failure. |
| Actual menu pages lacking a resolved child edge | **0** | Verified by parsing every stored page with the crawler's menu-link detector. |
| Source HTML has a Multipla diagram but no image record | **0** | Diagram references are captured even when the source image itself returns 404. |
| Extracted text contains site navigation markers | 2 | The two root URL variants lack article/list containers. |

## Validation

- Known unimported child URLs: **0**.
- A no-op resume run independently confirmed `pending_before=0` and `pending_after=0`.
- Six crawler regression tests pass.
- Python compilation and frontend JavaScript syntax checks pass.
- Meilisearch reports 6,951 documents and is not indexing.
- Component matching was rerun after crawl completion: 1,040 keyword attempts and 1,064 stored unique matches.
- Existing CURRENT GENERATOR article extraction and structured ignition subpages remain covered by regression tests.

## Remaining Phase 2A issues

1. Thirty-six unique diagram URLs are unavailable from the source and remain persisted as image failures.
2. The two root URL variants retain navigation text because the source provides no article/list content container.
3. Short-content heuristics remain unsuitable for automatic deletion because many valid pages are intentionally label- or image-led.

No ePER, Spareto, Alfa, wiring intelligence, CAD, MultiECUScan, AI, UI polish, or other Phase 2B work was added.
