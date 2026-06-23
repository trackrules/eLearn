# Phase 2A.6 Cutover Plan

## Current decision

Do not cut over yet. The disc release is staged and queryable, while the existing web-import tables remain the production source.

## Required approvals and gates

1. Review all unresolved comparison, unresolved target, missing-asset, disc-only-variant, and web-richer exceptions.
2. Recover or explicitly waive missing native assets; use the web crawl as fallback where its source asset ID fills a disc gap.
3. Validate applicability selection for production range, engine validity and CODEP combinations.
4. Expand rendering review beyond the six representatives, including diagnostic tables and complex wiring diagrams.
5. Define stable production URLs and redirects from web page IDs to disc element/XML IDs.
6. Build a reversible cutover migration and rehearse it against a database backup.
7. Reindex search from staged canonical text and compare search quality before promotion.
8. Obtain explicit approval before changing any production read path.

## Proposed cutover sequence after approval

Freeze the accepted staging release by database hash; resolve or accept exceptions; create compatibility views/API adapters; run a full regression and link/asset audit; snapshot production; enable the disc-backed read path behind a feature flag; monitor and compare; then retire web-primary reads only after rollback criteria remain clear.

Phase 2B must remain out of scope until this cutover is approved and complete.
