# Phase 2A.5 Full Comparison Report

The sample safety gate passed, so the complete manifests were compared outside the production database.

| Metric | Count |
|---|---:|
| Web pages compared | 6,951 |
| Disc XML records compared | 7,177 |
| exact match | 0 |
| likely same but different rendering | 4,177 |
| mismatch/needs manual review | 433 |
| same content, disc richer | 1,071 |
| same content, web richer | 1,268 |
| Web-only records | 2 |
| Disc-only candidates/unused XML variants | 3,955 |
| Unresolved cases | 433 |
| Referenced disc assets matched to web by source asset ID | 2,792 / 3,959 (70.5%) |
| Referenced disc assets matched to web by identical bytes | 0 / 3,959 (0.0%) |
| Missing referenced disc assets | 76 |
| Missing disc assets represented by a web source asset ID | 71 |
| Distinct web source asset IDs not present in disc manifest | 0 |
| Distinct web image hashes not byte-matched to disc | 2,755 |

## Interpretation

Direct source element IDs provide the strongest correspondence. Byte-level asset matching is intentionally strict: web PNG rendering of native disc SVG/JPEG does not produce the same hash, so a low byte-match rate is not evidence of different diagrams. Disc-only candidates include applicability variants and non-rendered records, not necessarily unique user-visible pages.

## Examples

- **likely same but different rendering:** - 4CarData; - 4CarData
- **same content, disc richer:** 2888504 - ENGINE - CHASSIS VERSION CODES; 2888514 -   ROUTINE MAINTENANCE PLAN
- **mismatch/needs manual review:** 2888740 -   10 ENGINE; 2892684 -   Introduction - FITTINGS
- **same content, web richer:** 2888747 -   50 AUXILIARY UNITS; 2888748 -   55 ELECTRICAL EQUIPMENT
- **web-only:** Fiat - MULTIPLA - eLearn - 4CarData; Fiat - MULTIPLA - eLearn - 4CarData
- **disc-only candidates:** XML 4385711 / Introduction - ENGINE; XML 4385724 / Introduction - PETROL INJECTION SYSTEM
