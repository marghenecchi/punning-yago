# General Analysis — Punning in YAGO

## Operational definition of punning

An entity E exhibits **punning** if and only if:

- E is used as a **class** in at least one triple (E rdf:type rdfs:Class, or E used as object of rdf:type)
- E is used as an **instance** in at least one triple (X rdf:type E, or E itself typed with rdf:type)

---

## How YAGO handles punning now (as far as i understood)

### Stage 02 (`02-make-taxonomy.py`)

An entity is added to the YAGO taxonomy (=becomes a class) if and only if:

1. It has 'wdt:P279' (subclass of) or 'wdt:P1709' (analogus class) in Wikidata, **AND**
2. It does **not** have any of the `instanceIndicators`:
   - `wdt:P171` — parent taxon
   - `wdt:P176` — manufacturer
   - `wdt:P178` — developer
   - `wdt:P580` — start time

If an entity has both P279 **and** P171 (e.g. a taxon that is also a subclass of something), the instance indicator win: it is treated as an instance and excluded from the class taxonomy.

### Stage 03 (`03-make-facts.py`)

If an entity is a YAGO class, it receives only `rdf:type rdfs:Class`. All Wikidata `P31` (instance of) statements on that entity are silently dropped. No entity in YAGO is simultaneously a class and a typed instance, the choice made in Stage 02 is ireversible.

### Taxonomy

Taxonomies have `P171` (parent taxon) → excluded from the class taxonomy at Stage 02. At Stage 03

All tax. become instances of `schema:Taxon`. The hierarchy is expressed via the `schema:parentTaxon` property (not `rdfs:subClassOf`). YAGO resolves taxon punning by flattening the hierarchy into a graph of instances, no taxon is a class.

### Stage 04 (`04-make-typecheck.py`)

One remaining case: a property expects an instance of class C, but the object in Wikidata is a class (subclass of C). YAGO handles this with a generic instance substitution:

A synthetic blank node `_:ClassName_generic_instance` is created and used in place of the class. The information that the object was a specific class is lost.

### Disjointness as a punning barrier

The top-level `owl:disjointWith` constraints catch cross-domain cases:

- An entity cannot be both a `schema:Person` and a `schema:Organization`
- An entity cannot be both a `schema:Taxon` and a `schema:Product`
- Facts violating these constraints are dropped and logged

## TODOs

- [x] Understand `02-make-taxonomy.py`
- [x] Same 4 `03-make-facts.py`
- [ ] Find other cases of `createGenericInstance' (lang, religion, ... ), how often does it trigger?
- [ ] What happens to products that are also brands (iPhone)? Does it have P279? If so, it becomes a class in YAGO, losing its instance facts
- [ ] How is `schema:Language` exactely handled, languages have P279 chains, so do they become YAGO classes or instances?
- [ ] P31/P279 ambiguity
- [ ] Are there cases where punning is desirable ? quali
- [ ] examples of real-world queries that fail because of the generic instance substitution or the binary class/instance choice
