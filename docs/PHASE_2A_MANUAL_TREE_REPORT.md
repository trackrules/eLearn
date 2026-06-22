# Phase 2A manual-tree report

Validation date: 2026-06-23

## Outcome

The completed Fiat Multipla import now has an eLearn-style tree browser alongside Search and Components.

Routes:

- `/manual`
- `/manual/fiat-multipla`
- `GET /api/manual/fiat-multipla/tree`
- `GET /manual/fiat-multipla/tree` on the backend

The primary navigation includes **Manual**. Existing Vehicle, Search, Components, and eLearn page routes remain available.

## Tree model

The API builds the tree from imported data only:

1. engine variant from breadcrumb segment 3;
2. top-level section from breadcrumb segment 4;
3. workshop/system category from the first later breadcrumb segment beginning with a two-digit system code;
4. page hierarchy from resolved `elearn_links.link_type='child'` edges;
5. `parent_page_id` as a relationship fallback;
6. breadcrumb grouping when either relationship is absent or crosses a group boundary.

Index and article nodes include title, ID, breadcrumb, category, direct child count, node kind, and locally available image count. Group nodes include unique page counts.

The UI uses native collapsible `details` elements. Index nodes both expand and link to `/elearn/:id`; leaves link directly to their imported eLearn page. Only the selected engine tree is rendered, and users can switch between `1.6 16V` and `1.9 JTD 8V`.

## Coverage returned by the API

| Engine | Pages | Sections |
|---|---:|---:|
| 1.6 16V | 3,604 | 6 |
| 1.9 JTD 8V | 3,343 | 6 |

The four vehicle/engine root records are intentionally outside the section tree. The endpoint returns 6,947 grouped manual pages from the 6,951-page import.

Both engines contain:

- TECHNICAL DATA
- DESCRIPTIONS
- FAULT DIAGNOSIS
- TEST
- PROCEDURES
- ELECTRICAL EQUIPMENT

## Acceptance branches

### Ignition tests

`1.6 16V > TEST > 55 ELECTRICAL EQUIPMENT > 5510 ENGINE IGNITION` resolves to imported page `425` and exposes exactly five direct children:

- 5510C coil, ecu, sensors (GPOWER)
- 5510CD Rpm sensor coil operation check (BIPOWER)
- 5510CE IGNITION CONTROL SIGNAL CHECK (BIPOWER)
- 5510CF RPM SIGNAL CHECK (BIPOWER)
- 5510OC IGNITION COIL RESISTANCE CHECK (BIPOWER)

### Current generator

The source breadcrumb places `Introduction - CURRENT GENERATOR` under:

`1.6 16V > DESCRIPTIONS > 55 ELECTRICAL EQUIPMENT > 5530 CURRENT GENERATOR`

The imported source relationship is preserved there (`229 > 1270`). The TECHNICAL DATA branch contains the imported 5530 tightening-torque page (`1116`) but no source parent edge to the introduction. To meet the requested technical-data workflow without altering database relationships, the API adds a clearly marked breadcrumb cross-reference when engine, system category, and four-digit manual code match. Therefore:

`1.6 16V > TECHNICAL DATA > 55 ELECTRICAL EQUIPMENT > 5530 CURRENT GENERATOR`

also exposes imported article `1270` as **Related description**.

## Validation

- Eight Python regression tests pass.
- Python compilation passes.
- Frontend JavaScript syntax validation passes.
- Manual API returns HTTP 200 in both `/api/...` and backend-direct forms.
- Manual API response: approximately 2.38 MB, generated locally in under one second.
- `/manual` and `/manual/fiat-multipla` return HTTP 200.
- `/search`, `/components`, and `/elearn/1270` still return HTTP 200.
- Search API for `5510CE` and Components API return HTTP 200.
- Actual-data assertions confirm both engines, all six sections, the five ignition children, the original generator relationship, and the technical-data generator cross-reference.

Rendered browser automation was unavailable in this session. Route responses, served frontend assets, JavaScript syntax, API payloads, and actual-data tree assertions were used for validation.

No Phase 2B features or new crawling were introduced.
