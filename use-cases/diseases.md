# Use Case: Diseases

## Example: COVID-19

---

## The two use cases

### UC1 — Taxonomy node with entity-level facts

COVID-19 is a subtype of coronavirus disease. We want to preserve this taxonomic relationship:

```turtle
:COVID-19  rdfs:subClassOf  :CoronavirusDisease .
:COVID-19  rdfs:subClassOf  :RespiratoryDisease .
```

At the same time, we want COVID-19 to carry facts about itself as a named disease entity:

```turtle
:COVID-19  :hasICD          "U07.1" .
:COVID-19  :causedBy        :SARS-CoV-2 .
:COVID-19  :firstReported   "2019-12-01"^^xsd:date .
```

These two requirements conflict: in any formalism where a node in the class hierarchy is a class, it cannot also carry instance-level properties. We do not need individual cases of COVID-19 in the KB, the use case is purely about COVID-19 as a named entity that is simultaneously part of the disease taxonomy and a carrier of medical facts.

### UC2 — Generic sentences

As in the animal example, we want to express facts that are true of the disease in general, not of every case:

```turtle
:COVID-19  :affects   :RespiratorySystem .
:COVID-19  :symptoms  :Fever .
:COVID-19  :symptoms  :Cough .
```

These are generic sentences: most COVID-19 cases affect the respiratory system, most present with fever or cough, but not all. Not reducible to universal quantification.

---

## The punning structure

COVID-19 in Wikidata has both:

- `wdt:P279` (subclass of): _coronavirus disease_, _respiratory disease_
- `wdt:P31` (instance of): _class of disease_, _disease_

The same entity must be:

- a class node in the taxonomy (so that the subclass chain is preserved)
- an instance carrying entity-level facts (ICD code, pathogen, date)

This pattern is systematic across the disease domain:

| Disease                  | P279 (subclass of)  | Entity facts wanted                       |
| ------------------------ | ------------------- | ----------------------------------------- |
| COVID-19                 | coronavirus disease | ICD code, pathogen, first reported date   |
| Influenza A              | influenza           | pathogen, seasonality, vaccine strains    |
| Diabetes mellitus type 2 | diabetes mellitus   | ICD code, risk factors, treatment options |
| Alzheimer's disease      | dementia            | ICD code, genetic markers, prevalence     |

Contrast with animals: in animals, the instanceIndicator (P171) forces Wolf to be an instance -> individual typing (UC1 in animals) fails. In diseases, P279 pushes COVID-19 into the taxonomy -> it becomes a class -> entity facts (UC1 here) are dropped. The same punning tension, opposite resolution in YAGO.

---

## Analysis by formalism

### RDF / RDFS

#### UC1 — Taxonomy node with entity-level facts

In RDF/RDFS there is no strict separation between classes and instances. Both roles can be expressed simultaneously:

```turtle
:COVID-19  rdfs:subClassOf  :CoronavirusDisease .   # taxonomy role
:COVID-19  :hasICD          "U07.1" .                # entity fact
:COVID-19  :causedBy        :SARS-CoV-2 .            # entity fact
```

No contradiction. Both are just triples.

If the schema declares `hasICD rdfs:domain Disease`, then rdfs2 infers `COVID-19 rdf:type Disease` — correct. The taxonomy chain and entity facts coexist without conflict in RDF/RDFS.

#### UC2 — Generic sentences

`COVID-19 affects RespiratorySystem` is writable. If `affects rdfs:domain Disease`, rdfs2 infers `COVID-19 rdf:type Disease` (correct). But the triple says nothing about individual cases, no propagation to instances. Same unsolvable problem as in the animals use case.

**Summary for RDF/RDFS:**

| Use case                     | Result              | Notes                                        |
| ---------------------------- | ------------------- | -------------------------------------------- |
| UC1: taxonomy + entity facts | ✓ coexist naturally | No class/instance barrier in RDF/RDFS        |
| UC2: generic sentences       | ✗ not propagated    | No mechanism to infer from kind to instances |

---

### OWL 2 DL

#### UC1 — Taxonomy node with entity-level facts

OWL 2 DL punning allows the two roles:

```turtle
-- Class role
:COVID-19  rdf:type        owl:Class .
:COVID-19  rdfs:subClassOf :CoronavirusDisease .

-- Individual role
:COVID-19  rdf:type   :Disease .
:COVID-19  :hasICD    "U07.1" .
:COVID-19  :causedBy  :SARS-CoV-2 .
```

The class and individual interpretations are in separate domains (ΔC and ΔI). Entity facts on the individual do not bleed into the class extension. Taxonomy membership is preserved via the class role. Both requirements satisfied.

#### UC2 — Generic sentences

Same problem as animals. `COVID-19 affects RespiratorySystem` as an ABox assertion on the individual says nothing about cases. Universal restriction too strong:

```turtle
:COVID-19  rdfs:subClassOf  (:affects some :RespiratorySystem) .
```

Not every case affects the respiratory system (asymptomatic cases, cases presenting primarily with other symptoms).

**Summary for OWL 2 DL:**

| Use case                     | Result              | Notes                            |
| ---------------------------- | ------------------- | -------------------------------- |
| UC1: taxonomy + entity facts | ✓ fully expressible | Punning separates roles cleanly  |
| UC2: generic sentences       | ✗ not expressible   | Universal restriction too strong |

---

### SHACL

TODO

---

## Summary table

| Formalism  | UC1: taxonomy + entity facts  | UC2: generic sentences               |
| ---------- | ----------------------------- | ------------------------------------ |
| RDF / RDFS | ✓ — no class/instance barrier | ✗ — no propagation to instances      |
| OWL 2 DL   | ✓ — punning separates roles   | ✗ — universal restriction too strong |
| SHACL      | TODO                          | TODO                                 |

---

## What YAGO does today

### How COVID-19 is processed

Stage 02 (`make-taxonomy.py`): COVID-19 has `wdt:P279` → added to `wikidataTaxonomyDown`. The instanceIndicator `wdt:P580` (start time) does not fire because P580 appears only as a qualified statement in the dump, not as a direct triple. COVID-19 enters the taxonomy.

Stage 03 (`make-facts.py`): COVID-19 is in the taxonomy → assigned `rdf:type rdfs:Class` → all entity-level facts are dropped. No `schema:MedicalCondition` exists in the YAGO 4.5 schema → COVID-19 has no type, no properties.

Verified: `yago:COVID-19 rdfs:subClassOf yago:Coronavirus_diseases` exists in `05-yago-final-taxonomy.tsv`. No entity facts in `05-yago-final-wikipedia.tsv`.

UC1 fails: taxonomy is preserved, but entity facts (ICD code, pathogen, date) are entirely lost.

### Capability table

| Desired capability                                                  | Status in YAGO | Reason                              |
| ------------------------------------------------------------------- | -------------- | ----------------------------------- |
| Taxonomy: `yago:COVID-19 rdfs:subClassOf yago:Coronavirus_diseases` | ✓ preserved    | P279 survives in taxonomy           |
| Entity: `yago:COVID-19 :hasICD "U07.1"`                             | ✗ dropped      | processed as class; no entity facts |
| Entity: `yago:COVID-19 :causedBy :SARS-CoV-2`                       | ✗ dropped      | same reason                         |
| Generic: `yago:COVID-19 :affects :RespiratorySystem`                | ✗ dropped      | no medical property in schema       |
| `?person yago:deathCause yago:COVID-19`                             | ✗ broken       | generic_instance substitution       |

Note: YAGO preserves the taxonomy role and loses everything else. The disease taxonomy in YAGO is navigable but carries no medical content.
