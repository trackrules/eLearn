# Fiat Multipla Disc Coverage Report

## Determination

Fiat Multipla content **definitively exists** on the mounted disc. This is established by actual records in every `D:\database\elearn_*.dat` file:

```text
MARK.ID          1
MARK.NAME        Fiat
MODEL.ID         2000006
MODEL.NAME       MULTIPLA
MODEL.CODE       186
MODEL_IMAGE      ./images/cars/fiat/multipla.jpg
```

The disc is a dedicated Multipla dataset, not a multi-vehicle database. The eight databases are eight language versions of the same vehicle.

## Languages

| Database | Language ID | Stored language name | Code | Character set | Element nodes | XML records |
|---|---:|---|---|---|---:|---:|
| `elearn_1.dat` | 1 | Italiano | IT | windows-1252 | 4,899 | 7,220 |
| `elearn_2.dat` | 2 | English | EN | windows-1252 | 5,111 | 7,177 |
| `elearn_3.dat` | 3 | German | DE | windows-1252 | 4,774 | 6,770 |
| `elearn_4.dat` | 4 | Spanish | ES | windows-1252 | 4,773 | 6,818 |
| `elearn_5.dat` | 5 | French | FR | windows-1252 | 4,800 | 6,849 |
| `elearn_6.dat` | 6 | Dutch | NL | windows-1252 | 4,772 | 6,819 |
| `elearn_7.dat` | 7 | Portoguese | PT | windows-1252 | 4,772 | 6,822 |
| `elearn_9.dat` | 9 | Polish | PL | windows-1250 | 4,809 | 7,035 |
| **Total physical localized records** |  |  |  |  | **38,710** | **55,510** |

Czech (ID 8), Greek (10), and Turkish (11) appear in the common language/help metadata but have no technical-content database on this disc.

## Production applicability

The six production ranges stored for Multipla are:

| Meaning/name as stored | Code | Italian ID | English ID | German ID | Spanish ID | French ID | Dutch ID | Portuguese ID | Polish ID |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fino a 05/99 | `Ì` | 2006000 | 2006007 | 2006014 | 2006021 | 2006028 | 2006035 | 2006042 | 2006056 |
| da 09/03 | `w` | 2006006 | 2006013 | 2006020 | 2006027 | 2006034 | 2006041 | 2006048 | 2006062 |
| da 06/99 a 03/02 | `1` | 2006200 | 2006202 | 2006204 | 2006206 | 2006208 | 2006210 | 2006212 | 2006216 |
| da 04/02 a 08/03 | `2` | 2006201 | 2006203 | 2006205 | 2006207 | 2006209 | 2006211 | 2006213 | 2006217 |
| da 06/04 | `z` | 186000000 | 186000000 | 186000000 | 186000000 | 186000000 | 186000000 | 186000000 | 186000000 |
| fino a 05/04 | `x` | 186000001 | 186000001 | 186000001 | 186000001 | 186000001 | 186000001 | 186000001 | 186000001 |

The production names remain Italian even in the English database; this is source data, not a reporting translation.

## Engine/version validity

Each language contains two validity records:

| Language | 1.6 16v ID | 1.9 JTD 8V ID |
|---|---:|---:|
| Italian | 2000600 | 2000601 |
| English | 2000602 | 2000603 |
| German | 2000604 | 2000605 |
| Spanish | 2000606 | 2000607 |
| French | 2000608 | 2000609 |
| Dutch | 2000610 | 2000611 |
| Portuguese | 2000612 | 2000613 |
| Polish | 2000616 | 2000617 |

The validity names are exactly `1.6 16v` and `1.9 JTD 8V` in all eight databases.

## Equipment/option applicability

Each database contains 21 `CODEP` option records. The Italian source names include:

- with/without ABS;
- automatic air conditioning and climate control;
- taxi preparation;
- ELX and SX trim;
- right-hand drive;
- GPOWER, BIPOWER, and BLUPOWER;
- supplementary heater/heater;
- Euro 3 variants;
- navigator and CONNECT;
- electric sunroof;
- ESP variants;
- head-bag.

Applicability is associated separately at navigation-element and XML-variant levels. In English alone there are 2,232 element–option and 2,913 XML–option relationships.

## Content by section and language

The first number is navigation `ELEMENT` rows; the second is source `XML` records.

| Language | Technical data | Descriptions | Diagnosis | Tests | Procedures | Electrical/wiring | Total XML |
|---|---:|---:|---:|---:|---:|---:|---:|
| Italian | 250 / 186 | 151 / 199 | 193 / 217 | 81 / 54 | 1,292 / 4,141 | 2,932 / 2,423 | 7,220 |
| English | 248 / 185 | 150 / 195 | 193 / 216 | 80 / 53 | 1,292 / 3,894 | 3,148 / 2,634 | 7,177 |
| German | 248 / 185 | 152 / 202 | 193 / 217 | 81 / 54 | 1,284 / 3,843 | 2,816 / 2,269 | 6,770 |
| Spanish | 248 / 185 | 150 / 195 | 193 / 216 | 81 / 54 | 1,292 / 3,894 | 2,809 / 2,274 | 6,818 |
| French | 248 / 185 | 153 / 202 | 193 / 216 | 81 / 54 | 1,294 / 3,900 | 2,831 / 2,292 | 6,849 |
| Dutch | 248 / 185 | 150 / 195 | 193 / 216 | 81 / 54 | 1,292 / 3,894 | 2,808 / 2,275 | 6,819 |
| Portuguese | 248 / 186 | 151 / 200 | 193 / 216 | 81 / 54 | 1,295 / 3,904 | 2,804 / 2,262 | 6,822 |
| Polish | 259 / 194 | 153 / 205 | 193 / 216 | 81 / 54 | 1,292 / 4,081 | 2,831 / 2,285 | 7,035 |
| **All languages** | **1,997 / 1,491** | **1,210 / 1,593** | **1,544 / 1,730** | **647 / 431** | **10,333 / 31,551** | **22,979 / 18,714** | **55,510** |

These are physical localized records. They should not be collapsed across languages without a tested translation-equivalence strategy because translated element/XML IDs differ.

## English coverage relevant to the current platform

The English source (`elearn_2.dat`) contains:

| Content class | Navigation nodes | XML records | Nodes with non-empty codes |
|---|---:|---:|---:|
| Technical Data | 248 | 185 | 0 |
| Descriptions | 150 | 195 | 98 |
| Fault diagnosis | 193 | 216 | 192 |
| Tests | 80 | 53 | 72 |
| Procedures | 1,292 | 3,894 | 1,255 |
| Electrical equipment/wiring | 3,148 | 2,634 | 3,147 |
| **Total** | **5,111** | **7,177** | **4,764** |

Examples from actual records:

| Class | XML ID | Element ID | Code | Name |
|---|---:|---:|---|---|
| Wiring | 4386585 | 2889028 | E3032 | DOOR MIRROR ADJUSTMENT - Wiring diagram |
| Procedure | 4388588 | 2891237 | 1036G20 | camshaft controlling intake valves in top head - r + r ... |
| Diagnosis | 4385913 | 2888312 | A01 | ALARM DOES NOT COME ON |

The diagnostic codes are eLearn workflow/symptom codes, not necessarily standardized OBD DTCs.

## Images and diagrams

The physical technical asset set is:

| Type | Count |
|---|---:|
| JPEG illustrations | 3,247 |
| Gzip-compressed SVG diagrams | 812 |
| Plain SVG diagrams | 5 |
| **Total** | **4,064** |

English XML references by section:

| Section | Unique asset IDs | XML records containing JPEG blocks | XML records containing SVG blocks |
|---|---:|---:|---:|
| Technical Data | 56 | 35 | 0 |
| Descriptions | 709 | 156 | 18 |
| Fault diagnosis | 3 | 0 | 0 |
| Tests | 49 | 35 | 16 |
| Procedures | 2,352 | 2,375 | 1,202 |
| Electrical/wiring | 811 | 0 | 591 |

Counts overlap because a native asset can appear in multiple records/sections. Wiring also uses `<conimageid>` component assets in addition to ordinary `<imageid>`.

Across all language databases:

- 104,881 image-ID occurrences are present (`94,754 imageid` and `10,127 conimageid`);
- 4,155 distinct IDs are referenced;
- all 4,064 physical disc assets are referenced;
- 91 referenced IDs have no file on the disc.

## Wiring and component coverage

English electrical XML contains:

- 2,634 wiring/electrical XML records;
- 591 records containing SVG blocks;
- 811 unique referenced asset IDs;
- 44,348 `targetid` occurrences;
- 640 unique target IDs;
- 806 unique values in structured `<code>` fields;
- explicit component tables, assembly references, earth/fuse codes, wiring functions, connector-image IDs, and links back to component nodes.

This is richer than a flat image/page corpus because the diagram, component code, component name, target node, and active vehicle applicability remain connected.

## Navigation and cross-link coverage

For English:

- six section roots;
- 5,111 distinct nodes;
- maximum tree depth four;
- no parent cycles;
- no orphan parents;
- no XML-to-element orphans;
- 54,169 cross-link target occurrences;
- 1,317 unique target IDs;
- 51,763 occurrences resolve to an existing element;
- 2,059 are deliberate page-local targets 0/1;
- 347 other occurrences are unresolved.

Polish has eight orphan parent rows; the other language trees are structurally clean.

## Comparison with current platform baseline

Current supplied platform metrics:

- 6,951 imported pages;
- 10,552 images;
- 1,064 component matches.

| Metric | Current platform | English disc source | Interpretation |
|---|---:|---:|---|
| Rendered pages / raw XML records | 6,951 pages | 7,177 XML records | Disc has 226 more raw records (+3.25%), but page and XML-variant units are not guaranteed one-to-one |
| Navigation nodes | Not supplied | 5,111 | Disc preserves the full hierarchy and node IDs |
| Images/assets | 10,552 | 4,064 native files disc-wide | Web count is higher, probably including duplicates, derivatives, UI assets, or repeated downloads; hash-level comparison is required |
| Component matches | 1,064 | 640 unique wiring target IDs; 806 structured wiring codes | Metrics differ; disc provides native identity/link structure rather than inferred matches |
| Production ranges | Not supplied | 6 | Disc has explicit applicability |
| Engine validities | Not supplied | 2 | Disc has explicit applicability |
| Equipment options | Not supplied | 21 | Disc has explicit applicability |
| Cross-links | Not supplied | 54,169 target occurrences | Disc preserves source relationships |
| Languages | Not supplied | 8 technical languages | Disc is multilingual |

The 226-record numeric surplus is evidence of potential crawl gaps, not proof of 226 additional user-visible pages. An exact claim requires the current platform's URL/node/content-hash manifest.

## Information richer than the web crawl

The disc contains information that cannot be reliably reconstructed from rendered pages alone:

- raw XML semantics and content grouping;
- section and navigation node IDs;
- ordered parent-child hierarchy;
- original `targetid` cross-links and structured codes;
- production, engine, and equipment applicability at two levels;
- original native SVG wiring/component diagrams;
- explicit image/component IDs;
- source language and encoding metadata;
- multilingual technical content;
- XSL renderer selection by section type.

## Coverage caveats

- 91 referenced asset IDs are missing from the physical disc.
- The disc has no content/update databases for Czech, Greek, or Turkish.
- There is no online update package on the mounted media.
- English production labels are unexpectedly Italian in the source.
- Some non-anchor cross-links are unresolved.
- The current 6,951-page dataset was not available for ID/hash-level matching during this inspection.

## Final coverage assessment

Multipla coverage is broad and internally structured: eight languages, six technical sections, six production ranges, two engine variants, 21 equipment options, 55,510 localized XML records, and 4,064 native technical assets. The disc is a richer canonical source than the web crawl for metadata, applicability, wiring, navigation, and original assets, while the web dataset remains necessary for parity validation and possibly for assets or later content absent from this 2004 disc.
