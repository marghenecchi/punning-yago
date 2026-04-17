# Punning Tests — Overview

Empirical tests for three punning use cases: animals, diseases, chemicals.
Each test answers the specific questions raised in the corresponding `use-cases/*.md` file.

---

## File structure

```
tests/
  animals/
    animals-schema.ttl          schema: classes + properties with domain/range
    animals-desired.ttl         the graph we want to express
    animals-yago-today.ttl      what YAGO actually stores
    animals-owl-restriction.ttl UC2 alternative: OWL class axiom for generic sentences
  diseases/
    diseases-schema.ttl
    diseases-desired.ttl
    diseases-yago-today.ttl
  chemicals/
    chemicals-schema.ttl
    chemicals-desired.ttl
    chemicals-yago-today.ttl
```

**`*-schema.ttl`** — classes and properties with `rdfs:domain`/`rdfs:range`. Used by RDFS
reasoners to fire inferences.

**`*-desired.ttl`** — what we want to write: the entity plays both the class role
(`rdfs:subClassOf`, `owl:Class`) and the individual role (`rdf:type`, property assertions).

**`*-yago-today.ttl`** — what YAGO actually stores after its pipeline: which facts survive,
which are dropped, and the generic instance substitution applied by Stage 04.

---

## How to run

```bash
# Syntax validation
riot --validate tests/animals/animals-desired.ttl

# SPARQL query (no inference — explicit triples only)
arq --data tests/animals/animals-schema.ttl \
    --data tests/animals/animals-desired.ttl \
    --query query.sparql

# RDFS closure (Python)
python3 -c "
import rdflib, owlrl
g = rdflib.Graph()
g.parse('tests/animals/animals-schema.ttl')
g.parse('tests/animals/animals-desired.ttl')
owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
"

# OWL RL closure (for OWL restriction tests)
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
```

---

## Animals

### UC1 — Individual typing: `?wolf rdf:type :Canis_lupus`

**Question**: can we type individual wolves against `Canis_lupus` while `Canis_lupus` is also a
class node in the taxonomy?

| Graph      | Query                                            | Result    |
| ---------- | ------------------------------------------------ | --------- |
| desired    | `SELECT ?w WHERE { ?w rdf:type ex:Canis_lupus }` | `Tito` ✓  |
| YAGO today | same                                             | _empty_ ✗ |

**Why YAGO fails**: Stage 02 fires `instanceIndicator` on `wdt:P171` (parentTaxon) → `Canis_lupus`
is excluded from the class taxonomy and processed as a plain instance of `schema:Taxon`. It has
no class role in YAGO — typing `Tito rdf:type Canis_lupus` is impossible.

With RDFS closure on the desired graph, rdfs9 propagates the full subclass chain to `Tito`:

| Inferred type | Via                                                                |
| ------------- | ------------------------------------------------------------------ |
| `Canis`       | rdfs9: `Tito rdf:type Canis_lupus`, `Canis_lupus subClassOf Canis` |
| `Canidae`     | rdfs9 transitive                                                   |
| `Animal`      | rdfs9 transitive                                                   |

This is correct and desirable — a wolf is an animal.

---

### UC2 — Generic sentences: `:Canis_lupus :eats :Deer`

**Question**: can we express "wolves eat deer" as a fact about the kind, and can we then query
"what does Tito eat?"

| Graph                  | Query                                               | Result                    |
| ---------------------- | --------------------------------------------------- | ------------------------- |
| desired (no inference) | `SELECT ?f WHERE { ex:Canis_lupus ex:eats ?f }`     | `Deer` ✓                  |
| desired (no inference) | `SELECT ?f WHERE { ex:Tito ex:eats ?f }`            | _empty_ ✗                 |
| desired (RDFS closure) | `SELECT ?f WHERE { ex:Tito ex:eats ?f }`            | _empty_ ✗                 |
| YAGO today             | `SELECT ?f WHERE { ex:Canis_lupus ex:consumes ?f }` | `Deer, Reindeer, Moose` ✓ |

**Why generic sentences do not propagate**: `:Canis_lupus :eats :Deer` is a triple on the
entity `Canis_lupus`, not a class axiom. RDFS has no rule that copies property values from a
class node to its instances — only `rdf:type` propagates via rdfs9. The query "what does Tito
eat?" returns empty even after full RDFS closure.

### UC2 alternative — OWL `someValuesFrom` restriction (`animals-owl-restriction.ttl`)

The only OWL mechanism that could propagate to instances is a class axiom:

```turtle
ex:Canis_lupus  rdfs:subClassOf
    [ owl:onProperty ex:eats ; owl:someValuesFrom ex:Deer ] .
```

| Graph           | Query                 | RDFS closure     | OWL RL closure   |
| --------------- | --------------------- | ---------------- | ---------------- |
| owl-restriction | `ex:Tito ex:eats ?f`  | _empty_          | _empty_          |
| owl-restriction | `ex:Bruno ex:eats ?f` | `CommercialFood` | `CommercialFood` |

Neither RDFS nor OWL RL propagates the restriction as explicit triples to individuals.

A full OWL DL reasoner would entail `Tito eats _:x`, `_:x rdf:type Deer`, but this might
have two problems:

1. **Too strong**: the restriction reads "every wolf eats at least one deer". Bruno, a wolf in
   captivity who only eats commercial food, would be entailed to also eat some anonymous deer —
   inconsistent with what we know.
2. **Anonymous witness**: the entailed object is a blank node `_:x` of type `Deer`, not the
   named individual `:Deer`. The query `?f WHERE { :Tito :eats :Deer }` would still return empty.

---

## Diseases

### UC1 — Entity facts on taxonomy node: `:COVID-19 :hasICD "U07.1"`

**Question**: can a disease entity carry medical facts (ICD code, pathogen, date) while also
being a node in the disease taxonomy?

| Graph      | Query                                          | Result      |
| ---------- | ---------------------------------------------- | ----------- |
| desired    | `SELECT ?c WHERE { ex:COVID_19 ex:hasICD ?c }` | `"U07.1"` ✓ |
| YAGO today | same                                           | _empty_ ✗   |

With RDFS closure on the desired graph, rdfs2 fires correctly:
`COVID_19 hasICD "U07.1"`, `hasICD rdfs:domain Disease` → `COVID_19 rdf:type Disease` ✓

**Why YAGO fails**: Stage 02 — `COVID-19` has `wdt:P279`, no instanceIndicator fires → enters
taxonomy as a class. Stage 03 — assigned `rdf:type rdfs:Class`, all entity facts fail the domain
check and are dropped. There is no `schema:MedicalCondition` in YAGO 4.5, so `COVID-19` receives
no `rdf:type` and no properties survive.

---

### UC2 — Generic sentences: `:COVID-19 :affects :RespiratorySystem`

Same problem as animals UC2. The triple is writable; RDFS correctly infers
`COVID_19 rdf:type Disease` and `RespiratorySystem rdf:type BodySystem` via rdfs2/rdfs3.
There are no individual cases in this use case (diseases.md explicitly excludes them),
so non-propagation is not tested here, see animals UC2 for that.

| Query                        | Result (desired, RDFS closure) |
| ---------------------------- | ------------------------------ |
| `ex:COVID_19 ex:affects ?s`  | `RespiratorySystem` ✓          |
| `ex:COVID_19 ex:symptoms ?s` | `Fever`, `Cough` ✓             |

## Chemicals

### UC1 — Entity facts on taxonomy node: `:H2O :CASNumber "7732-18-5"`

**Question**: can a chemical substance carry molecular data while also being a node in the
chemical taxonomy?

| Graph      | Query                                            | Result          |
| ---------- | ------------------------------------------------ | --------------- |
| desired    | `SELECT ?cas WHERE { ex:H2O ex:CASNumber ?cas }` | `"7732-18-5"` ✓ |
| YAGO today | same                                             | _empty_ ✗       |

**Why YAGO fails**: same mechanism as diseases — `H2O` has `wdt:P279`, no instanceIndicator,
enters taxonomy as class, all entity facts dropped. No `schema:ChemicalSubstance` in YAGO 4.5.

---

### UC2 — Pharmacological link: `:Prescription :prescribes :Aspirin`

**Question**: can a prescription link directly to Aspirin as a named drug?

| Graph      | Query                                        | Result                                         |
| ---------- | -------------------------------------------- | ---------------------------------------------- |
| desired    | `SELECT ?p ?d WHERE { ?p ex:prescribes ?d }` | `Prescription_42 → Aspirin` ✓                  |
| YAGO today | same                                         | `Prescription_42 → Aspirin_generic_instance` ✗ |
| desired    | `SELECT ?d ?c WHERE { ?d ex:treats ?c }`     | `Aspirin → Fever, Headache` ✓                  |
| YAGO today | same                                         | _empty_ ✗                                      |

Same generic instance substitution as diseases. The `treats` generic sentence also does not
propagate: "Aspirin treats Headache" says nothing about whether a specific prescription treats
headache.

---

### UC3 — ATC classification: multi-level punning

**Question**: can a classification hierarchy where each node is both an instance and a class
be expressed and queried?

| Graph      | Query                                              | Result      |
| ---------- | -------------------------------------------------- | ----------- |
| desired    | `SELECT ?c WHERE { ex:ATC_A ex:atcCode ?c }`       | `"A"` ✓     |
| desired    | `SELECT ?x WHERE { ex:ATC_A01 rdf:type ex:ATC_A }` | `ATC_A01` ✓ |
| YAGO today | `SELECT ?c WHERE { ex:ATC_A ex:atcCode ?c }`       | _empty_ ✗   |

With RDFS closure on the desired graph, the hierarchy propagates partially:

| Entity     | Inferred types                                                 |
| ---------- | -------------------------------------------------------------- |
| `ATC_A01`  | `ATCClassification`, `ATC_A` (explicit)                        |
| `ATC_A01A` | `ATC_A01`, `ATCClassification` (via rdfs2 on `atcCode` domain) |

`ATC_A01A rdf:type ATC_A` is **not** inferred: `ATC_A01` is typed as an _instance_ of `ATC_A`
(not a subclass via `rdfs:subClassOf`), so rdfs9 does not propagate further down. To get full
transitive typing across all ATC levels, `rdfs:subClassOf` between consecutive levels would be
needed — which is precisely the punning tension.

---

## Reasoner experiment: what happens if we attach properties directly to a class node?

**Question**: if `Canis_lupus` is a class and we attach properties to it directly — entity facts
and generic sentences — what does RDFS closure give us? Do properties propagate to instances?

Treat the class node as also an individual, write all triples on it, and run a reasoner.

**Setup** (`tests/reasoner_test.py`):

```python
# Canis_lupus as class node + entity facts + generic sentences
g.add((EX.Canis_lupus, RDF.type, OWL.Class))
g.add((EX.Canis_lupus, RDFS.subClassOf, EX.Canis))
g.add((EX.Canis_lupus, EX.conservationStatus, EX.LeastConcern))  # entity fact
g.add((EX.Canis_lupus, EX.eats, EX.Deer))                        # generic sentence
g.add((EX.Tito, RDF.type, EX.Canis_lupus))                       # individual wolf
owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
```

**Results**:

| Check                                                                  | Result |
| ---------------------------------------------------------------------- | ------ |
| `Canis_lupus rdf:type owl:Class` AND `rdf:type ex:Taxon` after closure | ✓      |
| `Canis_lupus ex:conservationStatus ex:LeastConcern` queryable          | ✓      |
| `Canis_lupus ex:eats ex:Deer` queryable                                | ✓      |
| `Tito rdf:type Canis` inferred (rdfs9 via subclass chain)              | ✓      |
| `Tito ex:eats ex:Deer` inferred                                        | ✗      |

**Why entity facts work but generic sentences do not propagate**:

RDFS has one rule that propagates information from a class to its instances: **rdfs9**.

```
rdfs9:  C rdfs:subClassOf D  +  x rdf:type C  →  x rdf:type D
```

This rule only propagates `rdf:type`. There is no analogous rule for other properties.
`Canis_lupus eats Deer` is a triple on the node `Canis_lupus` — RDFS has no rule that says
"if X is an instance of C, and C has property P, then X also has property P."

The asymmetry is intentional: `rdf:type` is safe to propagate because class membership is
definitional (if Tito is a wolf, he is by definition an animal). But `eats Deer` is not
definitional — it is a generic statement true of the kind in general, and individual wolves
may be exceptions (a wolf in captivity may eat only commercial food).

**OWL does not help either (TBD)**: the only OWL mechanism that could propagate to instances is
`owl:someValuesFrom`, which universalizes the statement ("every wolf eats at least one deer")
and produces anonymous blank node witnesses rather than the named individual `:Deer` (might not be a problem).
See the OWL restriction test in Animals UC2 above.

---

## Summary

| Use case                                            | Desired graph works? | YAGO today | Key failure mode                                   |
| --------------------------------------------------- | -------------------- | ---------- | -------------------------------------------------- |
| Animals UC1: `Tito rdf:type Canis_lupus`            | ✓                    | ✗          | instanceIndicator forces instance role, class lost |
| Animals UC2: generic sentence propagates to Tito    | ✗                    | ✗          | no such rule in RDFS or OWL                        |
| Diseases UC1: `COVID-19 hasICD "U07.1"`             | ✓                    | ✗          | P279 forces class role, entity facts dropped       |
| Diseases UC2: generic sentence writable on COVID-19 | ✓                    | ✗          | entity facts dropped in YAGO                       |
| Diseases UC3: direct `deathCause` link              | ✓                    | ✗          | Stage 04 generic instance breaks direct link       |
| Chemicals UC1: `H2O CASNumber "7732-18-5"`          | ✓                    | ✗          | same as diseases                                   |
| Chemicals UC2: direct `prescribes` link             | ✓                    | ✗          | same generic instance substitution                 |
| Chemicals UC3: ATC multi-level punning              | ✓ (partial)          | ✗          | rdf:type does not chain like subClassOf            |
