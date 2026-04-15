# Use Case: Animals / Taxonomies

## Example: Canis lupus

### The problem

Biological taxonomy is structuraly a system of nested classes, but each node is also an "instance" of the level above:

```
Kingdom: Animalia
  └── Class: Mammalia
        └── Order: Carnivora
              └── Family: Canidae
                    └── Genus: Canis
                          └── Species: Canis lupus    ← class of wolves OR instance of Canis?
                                └── Subspecies: Canis lupus familiaris
                                      └── [Tito]    ← concrete individual
```

The entity "Canis lupus" is used for three fundamentaly different kinds of statements:

| Statement                       | Type              | Subject is...          |
| ------------------------------- | ----------------- | ---------------------- |
| `Canis lupus parentTaxon Canis` | taxonomic fact    | the species-as-entity  |
| `Canis lupus eats deer`         | generic statement | the species-as-kind    |
| `Canis lupus is endangered`     | conservation fact | the species-as-kind    |
| `Tito rdf:type Canis lupus`     | instance typing   | Canis lupus as a class |

The beginning three look identical syntactically but the last one requires Canis lupus to be a class. The middle two are generic sentences, true of the kind but not necessarily of every individual ("wolves eat deer" admits the exception "my wolf doesn't eat deer").

### Special cases

- Extinct species: T-Rex exists as a class (all T-Rexes ever) but has no accessible concrete instances
- Species with a single known individual: the class has exactly one member
- Breeds: "Labrador Retriever" — breed as a class or instance of "dog breed"?

---

## How YAGO actually handles tax.

### Stage 02

Entities with `wdt:P171` (parent taxon) hit the `instanceIndicators` check and are excluded from the class taxonomy. They are never added to `yagoTaxonomyUp`, so they never become YAGO classes.

### Stage 03

Any entity with `schema:parentTaxon` gets `rdf:type schema:Taxon`. All taxa become instances, with the hierarchy expressed via `schema:parentTaxon` (a regular property, not `rdfs:subClassOf`):

```turtle
yago:Canis_lupus  rdf:type  schema:Taxon .
yago:Canis_lupus  schema:parentTaxon  yago:Canis .
yago:Canis_lupus  schema:name  "Canis lupus"@en .
```

The YAGO schema definition:

```turtle
schema:Taxon a sh:NodeShape, rdfs:Class ;
  rdfs:subClassOf schema:Thing ;
  owl:disjointWith schema:Person, schema:Organization, schema:Place,
                   schema:Event, schema:CreativeWork, schema:Product ;
  ys:fromClass wd:Q16521 ;
  sh:property [
    sh:path schema:parentTaxon ;
    sh:class schema:Taxon ;
    ys:fromProperty wdt:P171 ;
  ] .
```

### What YAGO can and cannot represent

- ✓ Taxonomic hierarchy (via `schema:parentTaxon`)
- ✓ Species-level facts as instance facts (`Canis lupus eats deer`, `Canis lupus is endangered`)
- ✗ Individual animals (`Tito rdf:type Canis_lupus` is impossible since Canis lupus is not a class)
- ✗ Distinction between generic statements and universal statements

---

## The generic sentence problem

`Canis lupus eats deer` in YAGO is a fact on the Canis lupus instance

- It does not mean every wolf eats deer (my wolf doesn't)
- It does not mean some wolf eats deer (too weak)
- It means wolves-as-a-kind have the disposition to eat deer

This is a generic predication. Generic sentences are:

- True of the kind even if not true of all members
- Not equivalent to universal or existential quantification
- Require the subject to be interpreted as a kind, not an individual

In YAGO, `Canis lupus eats deer` and `Canis lupus parentTaxon Canis` look the same, even though the first is a generic predication on a kind and the second is a taxonomic fact about an entity.

---

## The punning that remains

YAGO's "flatten to instances" solution eliminates one form of punning (Canis lupus as a class in the `rdfs:subClassOf` hierarchy) but introduces another: the Canis lupus entity is used both as:

1. A taxonomic entity: has a name, a parent taxon, a conservation status
2. A stand-in for the kind: for generic predications like "eats", "habitat", "behavior"

These two roles are conflated on a single instance node. TBD A proper solution here would maybe distinguish:

- `Canis_lupus_taxon` — the biological entity (parentTaxon, name, IUCN status)
- `Canis_lupus_kind` — the natural kind for generic predications (eats, habitat, lifespan)
- Individual wolves — instances, typed under `Canis_lupus_kind` TBD

This separation is i think what sescription logic tries to capture with TBox vs ABox, but DL doesn't fully solve for generics either (universal restrictions are too strong, they don't allow exceptions).

---

## Analysis by formalism

| Formalism     | How it handles it                                                                                                                                                                                                | Pros                             | Cons                                                                                                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RDF/RDFS      | same IRI as class and individual, both valid; generic facts stored as triples like entity facts                                                                                                                  | permissive                       | domain/range inference fires on class-level triples (e.g. `eats rdfs:domain Animal` → species becomes Animal instance); no distinction between generic and entity level |
| OWL 2 DL      | explicit punning via two-domain semantics: Canis lupus as class (extension of wolves) and individual (with parentTaxon, IUCN status) simultaneously; domain inferences on the individual do not affect the class | formally separates the two roles | generic facts still inexpressible: universal restriction `rdfs:subClassOf (eats some Deer)` is too strong; no OWL construct for tendential properties                   |
| Wikidata      | P31/P171 flat, generic facts on the species item                                                                                                                                                                 | pragmatic                        | no distinction between generic and universal                                                                                                                            |
| NCBI Taxonomy | pure IS-A, no instance facts                                                                                                                                                                                     | biologically correct             | not KR, ignores generic facts                                                                                                                                           |
| YAGO 4.5      | flatten tax. to instances, generic facts on taxon instance                                                                                                                                                       | avoids class punning             | conflates kind with individual, can't type individuals                                                                                                                  |

Note: the OWL 2 formalisms file (`formalisms/owl.md`) uses Canis lupus as its primary worked example for punning. The generic sentence problem (wolves eat deer) persists even with full OWL 2 two-domain semantics — no formalism in this list solves it.

---

## Why do we need class here?

Without Canis lupus as a class:

- Cannot type individual wolves (`Tito rdf:type Canis_lupus`)
- Cannot express that generic facts are about the kind, not the individual
- Cannot reason: "Tito is a wolf, wolves are a protected species, therefore Tito's species is protected"

With Canis lupus as a class only (no instance):

- Cannot attach facts to the species entity itself (parentTaxon, conservationStatus)
- This is the original punning problem

---

## Questions

- [ ] Does YAGO include individual animals at all, or only species?
- [ ] How are generic facts (eats, habitat) currently attached to tax. in YAGO?
- [ ] Could reification or named graphs distinguish generic vs universal predications on the same entity?
- [ ] Compare Wikidata vs NCBI Taxonomy treatment of the same taxon
