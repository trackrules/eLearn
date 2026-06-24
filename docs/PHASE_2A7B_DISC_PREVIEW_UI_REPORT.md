# Phase 2A.7B Disc Preview UI Report

## Scope

Phase 2A.7B adds a simple browser UI for the isolated English Fiat Multipla disc staging release. Every disc page displays **Disc Preview / Staged Source / Not Production**. The existing web-backed home, search, component, manual, and `/elearn/:id` routes remain separate and unchanged.

No production cutover, schema migration, Phase 2B feature, clickable SVG hotspot behavior, or additional vehicle/source integration was added.

## Frontend routes added

- `/disc` — staged-source explanation, validation shortcuts, counts, and disc search.
- `/disc/manual/fiat-multipla` — six-section manual tree with lazy child rendering and a client-side title/code filter.
- `/disc/elements/:element_id` — source identity, navigation, XML variants, applicability, and matched web pages.
- `/disc/xml/:xml_id` — safely rendered content, applicability, internal links, assets, matched web pages, and collapsed raw-source/debug data.

Existing routes `/`, `/search`, `/components`, `/components/radiator-fan`, and `/elearn/:id` returned HTTP 200 after the change.

## API endpoints used

The frontend Nginx service maps the internal `/disc-api/` prefix to the Phase 2A.7A backend `/disc/` routes. This avoids a collision between user-facing SPA routes and API routes with the same element/XML path shapes.

- `GET /disc/health`
- `GET /disc/manual/fiat-multipla/tree`
- `GET /disc/elements/{element_id}`
- `GET /disc/xml/{xml_id}`
- `GET /disc/assets/{asset_id}`
- `GET /disc/search?q=`

Element and XML responses now expose existing `disc_staging.web_disc_match` rows, and search also accepts an XML ID. No schema change was needed.

## Validation examples

| Section type | Element | XML | Result |
|---|---:|---:|---|
| Electrical equipment | 2888756 | 4386283 | Rendered; applicability returned |
| Test | 2892369 | 4392069 | Rendered; applicability returned |
| Descriptions | 2888218 | 4385717 | Rendered; applicability returned |
| Technical Data | 2888504 | 186015044 | Rendered; applicability and web matches returned |
| Fault diagnosis | 2888312 | 4385913 | Rendered; applicability returned |
| Procedures | 2891139 | 4388387 | Rendered; applicability returned |

Additional cases:

- JPEG: XML `4385712`, asset `2032733`; returned safely as `image/jpeg`.
- Gzipped SVG: XML `4386585`, asset `2033463`; exposed as an attachment-only native SVG asset without hotspot behavior.
- Missing asset: XML `4385722`, asset `2000041`; UI displays a missing-asset placeholder and the API returns structured `disc_asset_missing` JSON.
- Internal links: XML `4386954`; 114 resolved element references returned.
- Matched current web page: XML `186015114`; two current web matches returned.
- XML-ID search: query `186015044`; returned the matching Technical Data record.

The complete backend suite passed 17 tests, JavaScript syntax validation passed, Docker Compose configuration passed, and staged/production API smoke checks passed.

## Screenshots

Screenshots were not captured because the in-app browser was unavailable in this session. Route, proxy, data-shape, asset, and production-regression checks were completed over the running local HTTP services.

## Limitations

- This is a preview, not a production renderer or cutover path.
- The tree payload is loaded once, while DOM nodes are created lazily as branches open.
- Legacy SVG/gzipped SVG files with embedded DTD/entity declarations are download-only; no clickable diagram or hotspot logic is attempted.
- Search is intentionally basic and uses the existing staging data without a new index or schema.
- Raw source is shown only in a collapsed debug panel.

## Recommended next step

Obtain approval for the preview behavior, then perform a focused manual browser review with screenshots on representative desktop and mobile widths. Do not begin a production cutover or Phase 2B until the remaining staging exceptions and asset policy are explicitly accepted.
