# Wikidata Punning Analysis

## Goal

Quantify and characterize the punning phenomenon in Wikidata: how many entities are simultaneously `instance of` (P31) and `subclass of` (P279) of the same class and qualitatively how do they distribute?

The same node occupies two positions in the class hierarchy with respect to the same target.

I tried to do estimate how spread this phenomenon is but it always exceeded the time limit on both the qlever and wikidta query.

Here is an analysis on a limited sample of 10000 entities.

## Data collection

### SPARQL query (run on QLever)

```sparql
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?item ?itemLabel ?x ?xLabel
WHERE {
  ?item wdt:P31 ?x .
  ?item wdt:P279 ?x .
  ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
  ?x    rdfs:label ?xLabel    . FILTER(LANG(?xLabel)    = "en")
}
LIMIT 1000
```

Raw output: `query.csv` — 10 000 rows, single column `item` (QID URIs, no labels).

Note: the query as executed on QLever returned only the `?item` column; labels and `?x` were not
returned due to endpoint limitations. Labels and shared classes are recovered via `analyze.py`.

### Enrichment script

`analyze.py` reads `query.csv`, calls the Wikidata API in batches of 50, and for each item:

1. Fetches P31 and P279 claim values
2. Computes the intersection (shared class where both P31 and P279 point to same target)
3. Fetches English labels for items and shared classes
4. Writes `enriched.csv` and `summary.txt`

Run with:

```bash
python3 wikidata/analyze.py
```

## Results

Three successive runs with progressively cleaner queries (genes and bioinformatics artifacts excluded at SPARQL level). Latest run: **`summary-clean2.txt`** — 9000 items, **9090 pairs**, **934 distinct shared classes**, **8988 items with ≥1 shared class**.

### Bioinformatics noise — cumulative picture

Each run revealed a new dominant noise class:

| Class | QID | Count (clean2 run) | Pattern |
| ----- | --- | ------- | ------- |
| gene | Q7187 | excluded at SPARQL | gene variants P31+P279 → gene |
| non-coding RNA | Q427087 | excluded at SPARQL | same |
| protein | Q8054 | ~9784 (clean1 run) | specific proteins P31+P279 → protein |
| pseudogene | Q277338 | 5653 | same bioinformatics pattern |
| transfer RNA | Q201448 | 1153 | same |
| ribosomal RNA | Q215980 | 92 | same |

All six are systematic Wikidata bioinformatics modeling artifacts with no relevance to the YAGO punning problem. After excluding them: **~2200 meaningful pairs across ~928 classes**.

### Top shared classes (after bioinformatics noise)

| Shared class | QID | Count | Examples |
| ------------ | --- | ----- | -------- |
| bachelor's degree | Q163727 | 88 | Bachelor of Management, Bachelor of Nursing |
| Pride parade | Q51404 | 82 | Cologne Pride, EuroPride, Kreuzberg Pride |
| master's degree | Q183816 | 54 | Master of Education, Master of Social Work |
| food | Q2095 | 39 | ladyfinger, Tacacá, Scaccia |
| coin | Q41207 | 36 | Hercules ten franc coin, Stuiver, Klippe |
| aircraft | Q11436 | 27 | Breda A.14, Caproni-AV.I.S. C.4 |
| nerve | Q9620 | 24 | transverse cervical nerve, lesser occipital nerve |
| banknote | Q47433 | 23 | Norwegian banknote, 1 yen note |
| minister | Q83307 | 19 | Minister for Emergency Situations (Kazakhstan) |
| academic degree | Q189533 | 19 | honorary degree, Doctor of Philosophy |
| coat of arms | Q14659 | 18 | coat of arms of Chiapas, Rio de Janeiro |
| drink | Q40050 | 17 | yogurt drink, Perú Cola |
| color | Q1075 | 15 | Tuscan red, mauve, tangerine |
| organization | Q43229 | 15 | team, joint venture |
| electoral unit | Q192611 | 15 | canton of Nogent-le-Roi, university constituency |
| ATC code | Q192093 | 14 | ATC code A, ATC code D, ATC code J |
| school | Q3914 | 13 | combined school, leadership school |
| **disease** | **Q12136** | **13** | **olecranon bursitis, phakomatosis** |
| **genetic disease** | **Q200779** | **13** | **Microcephaly with spastic diplegia** |
| profession | Q28640 | 12 | bail bondsman, company security officer |
| software | Q7397 | 11 | software package, 360 Safeguard |
| stylistic device | Q182545 | 11 | isocolon, pleonasm |
| tribe | Q133311 | 10 | Visigoths, Zenata |
| military unit | Q176799 | 10 | March battalion, military staff |
| road | Q34442 | 9 | Voivodeship road, road in Japan |
| soup | Q41415 | 9 | ogbono soup, ohaw |
| spice | Q42527 | 9 | star anise, bay leaf, garlic powder |
| _(900+ classes with lower counts)_ | | | alcoholic beverage, laptop, Nobel Prize, … |

### Qualitative observations

#### Confirmed use cases

- **Diseases now appear**: `disease` (13) and `genetic disease` (13) directly confirm `diseases.md`. Specific diseases like phakomatosis are both instances of "disease" and subclasses.
- **Academic degrees** (bachelor's 88 + master's 54 + academic degree 19 = 161): the largest non-noise domain. Confirms `academic-disciplines.md` pattern at scale.
- **Event series**: Pride parade (82) — Cologne Pride, EuroPride are instances of "Pride parade" and subclasses (further editions are their instances). Nobel Prize (3) from clean1 run: Nobel Prize in Physics/Chemistry/Medicine are instances of Nobel Prize and subclasses. Directly confirms `event-series.md` stacked punning.
- **Products**: coin (36), aircraft (27), banknote (23), software (11), laptop (7), microprocessor (2) — confirms `products.md` at scale.
- **Colors** (15): natural kind with intrinsic class/instance hierarchy — candidate new use case.
- **Writing systems / languages**: cuneiform variants from earlier run — confirms `languages.md`.

#### New patterns not in existing use cases

- **ATC pharmaceutical codes** (14): ATC code A, D, J are both instances of the ATC classification system and subclasses (with sub-codes as instances). Clean taxonomy/entity punning in a professional classification system.
- **Coat of arms** (18): regional coats of arms are instances of "coat of arms" and subclasses (variants are instances of the specific coat). Similar to natural kinds.
- **Electoral units** (15): cantons, constituencies — administrative subdivisions used as both class nodes and named entities. Same pattern as `admin-divisions.md`.
- **Nerves / anatomy** (24): anatomical structures with named subtypes. New domain.
- **Minister** (19): specific ministerial roles (Minister for Police) as both instance and subclass of "minister". Could relate to `admin-divisions.md`.

#### Noise pattern

Wikidata bioinformatics ontologies systematically produce punning: every specific RNA/protein/pseudogene entry is modeled as both an instance of its class and a subclass (because further variants are typed against it). This is an artifact of how gene ontology data is imported into Wikidata — not semantic punning. Querying without excluding these classes will always return bioinformatics items first regardless of LIMIT.
