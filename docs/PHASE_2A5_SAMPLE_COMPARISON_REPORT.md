# Phase 2A.5 Sample Comparison Report

## Method

A deterministic, SHA-256-ranked stratified sample of 100 web pages covers all six technical sections plus pages with images, child pages, and component matches. Matching priority was source/node ID, exact normalized text hash, normalized title, then text/title/image similarity. The sample is reproducible from `tools/phase_2a5_compare.py`.

## Results

| Classification | Count |
|---|---:|
| likely same but different rendering | 77 |
| mismatch/needs manual review | 4 |
| same content, disc richer | 7 |
| same content, web richer | 12 |

The safety gate is **passed**: 96 of 100 sampled pages were linked without being classified web-only or unresolved.

## Representative examples

- **same content, disc richer** — 2889469 - E6020 AIR CONDITIONING - Location of components (Right hand drive) (`source/node ID`, score 0.6882)
- **same content, web richer** — 2888493 - X01 EXCESSIVE FUEL CONSUMPTION (`source/node ID`, score 0.7129)
- **likely same but different rendering** — DESCRIPTIONS - Fiat - MULTIPLA - eLearn - 4CarData (`source ID to disc section`, score 1.0)
- **mismatch/needs manual review** — 2892434 -   Introduction - LPG FUEL SYSTEM. (GPOWER) (`source/node ID`, score 0.5665)
- **same content, disc richer** — 186008490 - D020B Facia/rear junction (FACIA) (ELX setup, Right hand drive) (`source/node ID`, score 0.6675)
- **same content, web richer** — 186003489 - 5510CD Rpm sensor coil operation check (BIPOWER) (`source/node ID`, score 0.8056)
- **likely same but different rendering** — 10 ENGINE UNIT - Fiat - MULTIPLA - eLearn - 4CarData (`source/node ID to disc element`, score 1.0)
- **mismatch/needs manual review** — 2891515 - 1057B68 gpl injector unit with connection pipes to pressure regulator dismantle and rebuild at bench (GPOWER) (`source/node ID`, score 0.5695)
- **same content, disc richer** — 186008559 - F011 Right headlamp (FRONT) (`source/node ID`, score 0.6527)
- **same content, web richer** — 2888298 - 5560B analogue control panel (BIPOWER, BLUPOWER) (`source/node ID`, score 0.8317)

## Richness and gaps

- Web-richer sample matches: 12.
- Web-richer examples: 2888493 - X01 EXCESSIVE FUEL CONSUMPTION; 186003489 - 5510CD Rpm sensor coil operation check (BIPOWER); 2888298 - 5560B analogue control panel (BIPOWER, BLUPOWER).
- Disc-richer sample matches: 7.
- Sample web-only pages: 0.
- The disc has XML variants and applicability rows that do not map one-to-one to rendered web URLs; full comparison found 3,955 unused XML variants/records.
- Disc records not selected by a web match include: XML 4385711 / Introduction - ENGINE; XML 4385724 / Introduction - PETROL INJECTION SYSTEM; XML 4385725 / multi-point injection system (mpi).
- Confidence: **high** for source identity and hierarchy; content-richness labels are heuristic because the web renderer adds navigation text and may omit XML structure.
