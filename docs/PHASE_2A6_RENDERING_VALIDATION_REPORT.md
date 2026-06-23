# Phase 2A.6 Rendering Validation Report

## Security model

The proof-of-concept renderer uses Python's non-XSLT `ElementTree` parser, rejects DTD/entity declarations and active-content elements, applies an explicit HTML whitelist, escapes source text, and never resolves file or network resources. Links use the internal `disc://element/<id>` scheme and assets use `disc-asset://<id>`; no ActiveX, VBScript, JavaScript, external entity, external file, or network loading is available.

## Representative validation

| Section | Element | XML | Web page | Token similarity | Links rendered/source | Assets rendered/source |
|---|---:|---:|---:|---:|---:|---:|
| Electrical/Wiring | 2888764 | 4386301 | 2503 | 0.9915 | 2/2 | 1/1 |
| Tests | 2892686 | 4392082 | 859 | 0.9871 | 0/0 | 0/0 |
| Descriptions | 2892416 | 4385736 | 640 | 0.9122 | 0/0 | 1/1 |
| Technical Data | 2888515 | 186015114 | 131 | 0.9902 | 0/0 | 0/0 |
| Fault Diagnosis | 2888474 | 4386074 | 390 | 0.8980 | 0/0 | 0/0 |
| Procedures | 2891748 | 4389951 | 1917 | 0.9412 | 1/1 | 0/0 |

All six native section types rendered successfully. Internal source link and asset references were preserved in the output. Similarity is token-set Jaccard against the existing rendered web page and is evidence for content alignment, not pixel equivalence.

Rendered proof files and validation JSON are generated under ignored `data/exports/` paths and are not production UI assets.
