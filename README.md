# Fiat Multipla eLearn Phase 2A MVP

A focused proof-of-concept for the Interactive Fiat/Alfa Workshop & Parts Platform. This phase only supports **Fiat Multipla (eLearn code `186`)** and deliberately excludes Alfa, ePER import, Spareto links, MultiECUScan, CAD models, AI chat, interactive wiring intelligence, and user editing.

Pipeline:

```text
Fiat Multipla eLearn crawler -> PostgreSQL -> Meilisearch -> FastAPI -> simple dark UI
```

## Services

`docker-compose.yml` starts:

- PostgreSQL 16 on `localhost:5432`
- Meilisearch on `localhost:7700`
- FastAPI backend on `localhost:8000`
- Static frontend through nginx on `localhost:3000`

## Quick start

```bash
docker compose up --build -d
```

The first PostgreSQL boot automatically runs `backend/migrations/001_schema.sql`. If you need to run migrations again:

```bash
docker compose exec backend python -m app.cli migrate
```

Open the UI:

```text
http://localhost:3000
```

API health check:

```bash
curl http://localhost:8000/api/health
```

## Import workflow

Run these commands in order after the stack is up.

### 1. Crawl Fiat Multipla eLearn

```bash
docker compose exec backend python -m app.cli crawl
```

The crawler starts at `https://4cardata.info/elearn/186/2/`, follows only URLs under `/elearn/186`, stores raw HTML and parsed data, records links/images, and downloads Multipla diagram images into the backend storage volume.

To resume only unresolved child pages with a per-run safety limit:

```bash
docker compose exec backend python -m app.crawler --resume-pending --limit 500
```

Resume runs prioritize known child URLs, include newly discovered children in the same run, and persist run statistics, failed page/image URLs, and skipped URLs in `crawl_runs` and `crawl_url_events`.

Useful crawler environment variables in `docker-compose.yml`:

- `CRAWL_RATE_SECONDS` controls the polite delay between page requests.
- `CRAWL_MAX_PAGES` can be set for test crawls, for example `CRAWL_MAX_PAGES=20`.
- `IMAGE_STORAGE_DIR` controls where downloaded images are stored inside the backend container.

### 2. Rebuild the Meilisearch index

```bash
docker compose exec backend python -m app.cli reindex
```

Indexed fields are `id`, `title`, `breadcrumb`, `category`, `content_text`, `vehicle`, and `source_url`.

### 3. Seed Multipla components

```bash
docker compose exec backend python -m app.cli seed-components
```

Seeds these Phase 2A components and aliases:

- radiator fan
- coolant temperature sensor
- ABS pump
- engine ECU
- fuel pump
- crank sensor
- heater blower
- lambda sensor
- starter motor
- alternator

### 4. Link components to eLearn pages

```bash
docker compose exec backend python -m app.cli match-components
```

The matcher performs simple keyword matching across page title, breadcrumb, and body text. It stores match type, score, and matched text in `component_page_links`.

## UI routes

- `/` overview
- `/vehicles/fiat-multipla` vehicle status and import counts
- `/search` Meilisearch-backed eLearn search
- `/elearn/:id` imported eLearn page viewer with source URL, parsed text, and images
- `/components` seeded component list
- `/components/:slug` component detail page with aliases, related eLearn pages, related images, and placeholders for parts, wiring, fault codes, diagnostics, and CAD models

## Backend API routes

- `GET /api/vehicles`
- `GET /api/vehicles/fiat-multipla`
- `GET /api/search?q=radiator%20fan`
- `GET /api/elearn/{id}`
- `GET /api/components`
- `GET /api/components/{slug}`

## Database schema

The migration creates the Phase 2A tables:

- `vehicles`
- `elearn_pages`
- `elearn_images`
- `elearn_links`
- `components`
- `component_aliases`
- `component_page_links`

`elearn_pages.raw_html` preserves the original HTML so later phases can re-parse content without re-crawling.

## Troubleshooting

### PostgreSQL tables are missing

Run:

```bash
docker compose exec backend python -m app.cli migrate
```

If the database volume was created before the migration existed, reset local data with:

```bash
docker compose down -v
docker compose up --build -d
```

### Search is empty

Make sure pages have been crawled and then rebuild the index:

```bash
docker compose exec backend python -m app.cli crawl
docker compose exec backend python -m app.cli reindex
```

### Component pages show no related pages

Run the seed and matching jobs after crawling:

```bash
docker compose exec backend python -m app.cli seed-components
docker compose exec backend python -m app.cli match-components
```

### Crawler is slow

This is intentional. The crawler rate-limits requests to avoid hammering the source site. For a smoke test, set `CRAWL_MAX_PAGES` to a small value.

## Phase 2A assumptions and limitations

- The crawler treats `/elearn/186` as the Multipla boundary and refuses to queue other vehicle paths.
- Breadcrumb extraction is best-effort because the mirrored eLearn HTML can vary between pages.
- Parent/child relationships are inferred from crawl discovery order.
- Image downloads are best-effort; failed image URLs are logged in crawler output.
- Component matching is keyword-only and intentionally does not use AI.
- Imported data should be treated as internal research content pending legal review of the source material.

## Recommended Phase 2B next steps

- Add richer hierarchy browsing for systems and procedures.
- Normalize systems and engines from breadcrumbs.
- Add structured fault-code extraction where present.
- Improve component matching with domain-specific synonyms and negative-match handling.
- Add crawler run logs and a failed-URL retry table.
- Begin legal review before any public redistribution of imported content.
