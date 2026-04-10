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

#### Step 02 (`make-taxonomy.py`)

The `instanceIndicators` set includes `wdt:P176` (manufacturer) and `wdt:P178` (developer):

```python
instanceIndicators = {
    "wdt:P171",  # parent taxon -> instance of taxon
    "wdt:P176",  # manufacturer -> instance of Product
    "wdt:P178",  # developer -> instance of Product
    "wdt:P580"   # start time -> instance of Event
}
```

Both iPhone (Q11922) and iPhone 13 (Q108118280) have `wdt:P176` (manufacturer: Apple) in Wikidata. The instanceIndicator fires for both. Neither enters `yagoTaxonomyDown`, so neither becomes a YAGO class.

#### Step 03 (`make-facts.py`)

Since neither entity is in `yagoTaxonomyUp`, `make-facts.py` tries to assign a type via `wdt:P31`:

```python
TYPE_PREDICATES = [Prefixes.wikidataType, ...]  # wdt:P31, occupation, genre, position

for obj in entityFacts.objectsOf(mainEntity, predicate):
    if obj in yagoTaxonomyUp:          # only if the type is itself a YAGO class
        entityFacts.add((mainEntity, Prefixes.rdfType, obj))
```

The problem is that specific product models in Wikidata are primarily described via `wdt:P279` (subclass of the product line), not via `wdt:P31`. `wdt:P279` is not in `TYPE_PREDICATES` — it is never used for typing instances. So:

- iPhone's `wdt:P31` = "product line" (Q1366112) — not a YAGO class → no type
- iPhone 13's `wdt:P31` is either absent or maps to something not in `yagoTaxonomyUp` → no type

In both cases, `types` is empty:

```python
if not types:
    self.writer.writeMetaFact(mainEntity, Prefixes.rdfType, Prefixes.schemaThing,
                              Prefixes.ysReason, '"no valid type among ..."')
    return True
```

Both entities are written only to the meta file as `schema:Thing` with reason `"no valid type"`. Neither appears in the main YAGO facts.

---

### The double failure

The `instanceIndicators` mechanism was designed to protect products: if an entity has a manufacturer, treat it as an instance (not a class). The intent is correct. But in practice in this case the mechanism produces a double failure:

1. **Step 02**: the instanceIndicator fires correctly — iPhone and iPhone 13 are excluded from the class taxonomy, which is the right call.
2. **Step 03**: both entities need a valid type via `wdt:P31`. But `wdt:P31` for specific product models either points to meta-categories ("product line") that are not YAGO classes, or is absent entirely. `wdt:P279` (the natural typing chain for products) is never consulted for instance typing.

Result: both iPhone and iPhone 13 disappear from YAGO entirely.

| Entity    | Has P176? | Excluded from taxonomy? | P31 maps to YAGO class? | YAGO result          |
| --------- | --------- | ----------------------- | ----------------------- | -------------------- |
| iPhone    | Yes       | Yes                     | No ("product line")     | meta only, invisible |
| iPhone 13 | Yes       | Yes                     | No (absent or unmapped) | meta only, invisible |

This is worse than the disease case: COVID-19 ends up as a useless class but at least survives in YAGO. Products with a manufacturer are actively excluded from the taxonomy and then fail to be typed as instances.

---

### Root cause: second-order classes

In Wikidata, specific product models are typed as instances of **second-order classes**, classes whose instances are themselves classes:

```
iPhone 13  --wdt:P31-->  "smartphone model"  --wdt:P31-->  second-order class (Q24017414)
```

"Smartphone model" is a class of product models (each of which is a class of individual units). It is not a class of physical objects. YAGO explicitly excludes second-order classes and all their descendants:

```python
badClasses = {
    ...
    "wd:Q24017414",   # second-order class
    ...
}
# Classes that will not be added to YAGO, and whose children won't be added either
```

"Smartphone model" is a child of a `badClass` → excluded from `yagoTaxonomyUp`. So when `make-facts.py` checks `if obj in yagoTaxonomyUp` for iPhone 13's `wdt:P31 = "smartphone model"`, the check fails. No type is assigned.

This is correct behavior from YAGO's perspective: "smartphone model" is genuinely a second-order class (a class of classes), and YAGO is right to exclude it. But the side effect is that iPhone 13, whose only `wdt:P31` leads through a second-order class, ends up with no valid type and disappears.

---

### What would fix it TBD

One option: add `wdt:P279` to `TYPE_PREDICATES` for entities that have been excluded from the taxonomy via instanceIndicators. If iPhone 13 has `wdt:P279` pointing to iPhone, and iPhone (despite having P176) was not added to the taxonomy, then climb the P279 chain until a YAGO class is found (e.g., smartphone → schema:Product).

Another option: add "product line" (Q1366112) and similar meta-categories to the YAGO taxonomy so that their subtypes become valid YAGO classes, but this risks re-introducing the punning problem by making product lines into classes again.

A third option (analogous to biological taxonomy): add a `yago:productLine` property on the `schema:Product` shape to preserve the P279 link at the instance level, independently of typing. But this requires the parent entity (iPhone) to survive make-facts.py, which it currently does not.

---

### Comparison with biological taxonomy

|                                   | Bio-taxonomy (Canis lupus)         | Product (iPhone 13)                            |
| --------------------------------- | ---------------------------------- | ---------------------------------------------- |
| Is the class role useful?         | Yes, individual wolves exist       | Unlikely, individual units are not in YAGO     |
| Are entity-level facts important? | Yes (parentTaxon, IUCN status)     | Yes (manufacturer, date, price, GTIN)          |
| Is the hierarchy preserved?       | Yes, via `schema:parentTaxon`      | No, P279 chain is not used for instance typing |
| YAGO's choice                     | instance (flatten to taxon)        | intended: instance — actual: invisible         |
| Information lost                  | cannot type individual wolves      | the entity disappears entirely                 |
| Mechanism                         | dedicated instanceIndicator (P171) | instanceIndicators (P176, P178) + P31 failure  |

---

### Analysis by formalism

| Formalism  | How it handles it                                                                                                                                                                                                    | Pros                        | Cons                                                                                                                                                                                                                                                                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RDF/RDFS   | P279 and P31 coexist; entity facts (manufacturer, release date) coexist with class triples (subClassOf product line); domain/range inference fires on entity facts                                                   | permissive                  | products introduce **three-level punning** (product line → model → unit): each level is simultaneously a class of the level below and an instance of the level above; RDFS has no mechanism to annotate which level a triple belongs to; generic facts ("iPhone 13 has 12MP camera") are indistinguishable from entity facts ("iPhone 13 was released in 2021") |
| OWL 2      | two-domain punning: iPhone 13 as class (of units) and individual (with manufacturer, date); each level of the three-level hierarchy handled independently; the class and individual interpretations do not interfere | formally complete per level | three-level hierarchy requires stacked punning: iPhone (class + individual) contains iPhone 13 (class + individual) — the two levels are semantically independent, and OWL 2 provides no way to express the hierarchical relationship between them as both classes and individuals simultaneously                                                               |
| Wikidata   | P31 + P279 co-exist, manufacturer on the item                                                                                                                                                                        | pragmatic, data-rich        | no single interpretation; both roles co-exist                                                                                                                                                                                                                                                                                                                   |
| GS1 / GTIN | product classes (GTIN prefixes) vs. individual items (serial numbers)                                                                                                                                                | commercially precise        | no RDF-native representation                                                                                                                                                                                                                                                                                                                                    |
| YAGO 4.5   | instanceIndicator fires correctly, but P31 fails → entity disappears                                                                                                                                                 | intent correct              | product entities vanish from the KB                                                                                                                                                                                                                                                                                                                             |

Note: the product case is unique in having both the deepest punning hierarchy (three levels) and a specific Wikidata modeling issue: product models are typed as instances of **second-order classes** (classes whose instances are themselves classes), which YAGO explicitly excludes via `badClasses`. This double exclusion (instanceIndicator + badClass via P31 chain) is the root cause of the double failure, and is a structural property of how commercial products are modeled in Wikidata.

---

### Why do we need class here?

Without iPhone 13 as a class:

- Cannot type individual units as `rdf:type yago:iPhone_13`
- But: individual units are not in YAGO, so this is a theoretical loss

Without iPhone 13 as an instance:

- Cannot attach manufacturer, release date, dimensions, price, GTIN
- This is a real loss, these are the core facts one wants about a product

**Verdict**: YAGO's intent to make iPhone 13 an instance is correct. But the implementation fails: the instanceIndicator excludes the entity from the taxonomy, and then the P31-based typing cannot recover it because Wikidata encodes product models primarily via P279, not P31. The entity disappears. The fix requires either consulting P279 for instance typing (when P31 fails), or re-examining which Wikidata meta-categories ("product line", "smartphone model") should be brought into the YAGO taxonomy.

---

## Questions

- [ ] Is there any product that successfully becomes a `schema:Product` instance in YAGO? What P31 does it have?
- [ ] Would adding `wdt:P279` to the instance-typing logic (as a fallback when P31 fails) fix the product disappearance, and would it introduce any undesired side effects?
- [ ] Should "product line" (Q1366112) and "smartphone model" be added to the YAGO taxonomy, so their P279-children get valid types?
- [ ] How does the `schema:isVariantOf` property in schema.org relate to the product-line / model distinction?
- [ ] How does GS1's GTIN hierarchy (brand + product class + item reference) compare to Wikidata's P279 chain for products?
