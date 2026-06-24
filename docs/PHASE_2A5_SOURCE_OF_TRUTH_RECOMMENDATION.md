# Phase 2A.5 Source-of-Truth Recommendation

## Decision

**B. Disc canonical after specific fixes**

1. **Can the disc become canonical?** Yes, after an exceptions layer is defined for 76 missing referenced English assets, 433 unresolved comparisons, and verified web-only records. The disc preserves native XML, ordered hierarchy, source IDs, applicability, cross-links, and native asset identity.
2. **Should the web crawl become validation/fallback only?** Yes. Retain the current crawl snapshot as reconciliation evidence and a fallback for confirmed gaps, rather than treating rendered HTML as the primary record.
3. **Reasons to keep the crawler primary?** None strong for this fixed 2004 corpus. It loses structured applicability and source semantics. Keep crawler code operational only for validation, later-source detection, and gap recovery.
4. **Disc gaps filled by web?** Yes for assets: 71 of the 76 referenced-but-missing English disc asset IDs are represented in the web crawl. The only 2 web-only records are duplicate top-level wrappers, and there are 0 web source asset IDs outside the English disc manifest. The 2,755 unmatched web image byte hashes are not direct evidence of different content because the crawl stores PNG renderings of native SVG/JPEG.
5. **Safest migration strategy:** version the extractor; load disc data into isolated staging tables/database; preserve raw XML and hashes; build explicit exceptions; reconcile web URLs to disc element/XML IDs; validate counts, samples, assets, links and applicability; only then perform an atomic production cutover with rollback.
6. **Before Phase 2B:** manually review all web-only/unresolved cases, classify missing assets, add semantic image comparison for rendered SVG/JPEG, validate XML rendering against representative pages, document applicability selection rules, and rerun tests from a clean staging restore.

No production import or Phase 2B work occurred in this phase.
