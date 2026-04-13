# Use Case: Products

## Example: iPhone 13

### The problem

In Wikidata, iPhone 13 (Q108118280) carries simultaneously:

- `wdt:P279` (subclass of): _iPhone_ (the product line)
- `wdt:P31` (instance of): _smartphone_, _consumer electronics product_
- `wdt:P176` (manufacturer): _Apple Inc._

This is classic punning: the same entity is used as a class ("every iPhone 13 unit is an iPhone 13") and as an instance (it has a release date, dimensions, a price, a manufacturer).

The pattern is systematic across the product domain:

| Product                   | P279 (subclass of)           | P31 (instance of)            | P176 (manufacturer) |
| ------------------------- | ---------------------------- | ---------------------------- | ------------------- |
| iPhone 13                 | iPhone (product line)        | smartphone, consumer product | Apple Inc.          |
| Tesla Model 3             | Tesla Model 3 (product line) | electric vehicle             | Tesla, Inc.         |
| AstraZeneca COVID vaccine | COVID-19 vaccine             | vaccine, biopharmaceutical   | AstraZeneca         |
| LEGO Technic 42099        | LEGO Technic (product line)  | toy, construction set        | LEGO Group          |

---

### The three-level hierarchy

Products generally have a structure in three levels:

```
Product line: iPhone
  └── Model: iPhone 13           ← class of all iPhone 13 units OR instance of iPhone?
        └── Unit: iPhone 13 #A1234  ← a concrete individual device
```

Each level gives rise to different statements:

| Statement                        | Type              | Subject is...             |
| -------------------------------- | ----------------- | ------------------------- |
| `iPhone 13 subClassOf iPhone`    | taxonomic fact    | the model as a sub-kind   |
| `iPhone 13 manufacturer Apple`   | instance fact     | a specific product entity |
| `iPhone 13 dateCreated 2021`     | instance fact     | a specific product entity |
| `iPhone 13 has 12MP camera`      | generic statement | the model-as-kind         |
| `unit #A1234 rdf:type iPhone_13` | instance typing   | iPhone 13 as a class      |

The first four look syntactically identical but require different interpretations. The last one requires iPhone 13 to be a class.

---

### How YAGO handles it

_Empirically verified against `05-yago-final-wikipedia.tsv` on 2026-04-13. The previous analysis here predicted a "double failure" where both entities disappear, this was totally incorrect._

#### Step 02 (`make-taxonomy.py`)

`wdt:P176` (manufacturer) fires the instanceIndicator for both iPhone (Q2766) and iPhone 13 (Q108118280). Neither enters the taxonomy as a class.

#### Step 03 (`make-facts.py`)

P31 typing succeeds: `yago:Smartphone_Model` and `yago:Smartphone_Model_Series` are in `yagoTaxonomyUp` (not excluded by `badClasses`), so both entities get valid types and their entity facts are preserved.

```turtle
yago:IPhone       rdf:type    yago:Smartphone_Model_Series .
yago:IPhone       schema:url  "https://en.wikipedia.org/wiki/IPhone" .
yago:IPhone       rdfs:label  "iPhone"@en .

yago:IPhone_13    rdf:type              yago:Smartphone_Model .
yago:IPhone_13    schema:manufacturer   yago:Apple_Inc .
yago:IPhone_13    schema:dateCreated    "2021-09-14"^^xsd:date .
yago:IPhone_13    schema:price          "+909"^^yago:Euro .
yago:IPhone_13    schema:height         "+146.7"^^yago:Millimetre .
```

The taxonomy chain: `yago:Smartphone_Model_Series rdfs:subClassOf yago:Mobile_Phone_Series`.

The instanceIndicator mechanism works correctly for products: both entities are instances with their entity-level facts preserved, not classes. The class role (typing individual physical units) is dropped, but individual units are not in YAGO anyway.

### Comparison with biological taxonomy

|                                   | Bio-taxonomy (Canis lupus)         | Product (iPhone 13)                              |
| --------------------------------- | ---------------------------------- | ------------------------------------------------ |
| Is the class role useful?         | Yes, individual wolves exist       | No, individual units are not in YAGO             |
| Are entity-level facts important? | Yes (parentTaxon, IUCN status)     | Yes (manufacturer, date, price)                  |
| Is the hierarchy preserved?       | Yes, via `schema:parentTaxon`      | Partially — model series hierarchy exists        |
| YAGO's choice                     | instance (flatten to taxon)        | instance (instanceIndicator + P31 typing)        |
| Information lost                  | cannot type individual wolves      | cannot type individual units; color links broken |
| Mechanism                         | dedicated instanceIndicator (P171) | instanceIndicators (P176, P178) + P31 success    |

---

### Analysis by formalism

| Formalism  | How it handles it                                                                                                                                                                                                    | Pros                        | Cons                                                                                                                                                                                                                                                                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RDF/RDFS   | P279 and P31 coexist; entity facts (manufacturer, release date) coexist with class triples (subClassOf product line); domain/range inference fires on entity facts                                                   | permissive                  | products introduce **three-level punning** (product line → model → unit): each level is simultaneously a class of the level below and an instance of the level above; RDFS has no mechanism to annotate which level a triple belongs to; generic facts ("iPhone 13 has 12MP camera") are indistinguishable from entity facts ("iPhone 13 was released in 2021") |
| OWL 2      | two-domain punning: iPhone 13 as class (of units) and individual (with manufacturer, date); each level of the three-level hierarchy handled independently; the class and individual interpretations do not interfere | formally complete per level | three-level hierarchy requires stacked punning: iPhone (class + individual) contains iPhone 13 (class + individual) — the two levels are semantically independent, and OWL 2 provides no way to express the hierarchical relationship between them as both classes and individuals simultaneously                                                               |
| Wikidata   | P31 + P279 co-exist, manufacturer on the item                                                                                                                                                                        | pragmatic, data-rich        | no single interpretation; both roles co-exist                                                                                                                                                                                                                                                                                                                   |
| GS1 / GTIN | product classes (GTIN prefixes) vs. individual items (serial numbers)                                                                                                                                                | commercially precise        | no RDF-native representation                                                                                                                                                                                                                                                                                                                                    |
| YAGO 4.5   | instanceIndicator fires correctly, P31 typing succeeds → entities survive as instances with facts; colors replaced by generic instances                                                                              | works for entity facts      | three-level hierarchy flattened; color/attribute links broken by generic instances                                                                                                                                                                                                                                                                              |

---

### Why do we need class here?

Without iPhone 13 as a class:

- Cannot type individual units as `rdf:type yago:iPhone_13`
- But: individual units are not in YAGO, so this is a theoretical loss

Without iPhone 13 as an instance:

- Cannot attach manufacturer, release date, dimensions, price, GTIN
- This is a real loss, these are the core facts one wants about a product

**Verdict**: YAGO handles products correctly as instances, entity facts (manufacturer, price, dimensions, date) are preserved. The class role (typing individual physical units) is dropped, but this is a trade-off since individual units are not in YAGO.

---

## Questions

- [ ] Is there any product that successfully becomes a `schema:Product` instance in YAGO? What P31 does it have?
- [ ] How does the `schema:isVariantOf` property in schema.org relate to the product-line / model distinction?
- [ ] How does GS1's GTIN hierarchy (brand + product class + item reference) compare to Wikidata's P279 chain for products?
