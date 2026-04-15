# Use Case: Animals / Biological Taxonomy

## Example: Canis lupus (wolf)

---

## The two use cases

### Individual typing

We want to be able to type individual wolves against their species:

```turtle
:Tito  rdf:type  :Canis_lupus .
```

This requires `Canis_lupus` to be a class. At the same time, we want `Canis_lupus` to carry entity-level facts as an instance:

```turtle
:Canis_lupus  rdf:type        :Taxon .
:Canis_lupus  :parentTaxon    :Canis .
:Canis_lupus  :conservationStatus  :LeastConcern .
```

This is the main punning problem: `Canis_lupus` must be both a class (so Tito can be typed) and an instance of `Taxon` (so it can carry taxon-level facts). In YAGO today this is impossible — `wdt:P171` (parentTaxon) is an `instanceIndicator` that forces Wolf to be an instance only.

### UC2 — Generic sentences

We want to express facts that are true of the kind, not of all individual members:

```turtle
:Canis_lupus  :eats    :Deer .
:Canis_lupus  :livesIn :Forest .
```

These are generic sentences: true in general, with exceptions allowed. The intended meaning is not "all wolves eat deer" (too strong) nor "some wolf eats deer" (too weak), but "wolves typically eat deer".

Generic sentences cannot be reduced to any standard logical form:

| Candidate translation | Formula                           | Problem                                               |
| --------------------- | --------------------------------- | ----------------------------------------------------- |
| Universal             | `∀x Wolf(x) → eats(x, Deer)`      | Too strong — false for wolves that don't eat deer     |
| Existential           | `∃x Wolf(x) ∧ eats(x, Deer)`      | Too weak — says nothing about the kind                |
| Majority              | `most x: Wolf(x) → eats(x, Deer)` | Not expressible in RDF/OWL                            |
| Default               | generic rule with exceptions      | Requires non-monotonic reasoning, outside standard KR |

**This use case is a universal problem, not specific to YAGO, not really solvable in any standard formalism.**

---

## Analysis by formalism

### RDF / RDFS

#### UC1 — Individual typing

RDF syntactically allows `Tito rdf:type Canis_lupus` regardless of whether `Canis_lupus` is also used as an instance. There is no class/instance distinction at the syntactic level — any IRI can appear in any position.

So both triples are writable:

```turtle
:Canis_lupus  rdf:type  :Taxon .   # instance
:Tito         rdf:type  :Canis_lupus .  # class use
```

No contradiction. Individual typing works in RDF/RDFS.

However, RDFS inference conflates the two roles. If the schema declares:

```turtle
:parentTaxon  rdfs:domain  :Taxon .
```

then rule **rdfs2** fires on `Canis_lupus parentTaxon Canis` and infers `Canis_lupus rdf:type Taxon`. Then rule **rdfs9** fires on `Tito rdf:type Canis_lupus` combined with any `Canis_lupus rdfs:subClassOf X` axiom, propagating types to Tito. The chain works, but without semantic separation between the class role and the instance role of `Canis_lupus`.

#### UC2 — Generic sentences

The triple `:Canis_lupus :eats :Deer` is syntactically valid. The problem is what RDFS infers from it.

If the schema declares:

```turtle
:eats  rdfs:domain  :Animal .
```

then rule **rdfs2** fires:

```
:eats rdfs:domain :Animal  +  :Canis_lupus :eats :Deer
→  :Canis_lupus rdf:type :Animal
```

RDFS infers that `Canis_lupus` is an Animal, treating it as an individual animal, not as a class. This is semantically wrong: we meant that _members_ of the class eat deer, not that the class itself is an animal.

RDFS has no mechanism to distinguish "this triple is about the kind" from "this triple is about an individual". The domain inference fires regardless of intent.

Additionally, the generic sentence says nothing about individual wolves. Even with `Tito rdf:type Canis_lupus`, RDFS cannot infer `Tito eats Deer` from `Canis_lupus eats Deer` — there is no rule that propagates ABox facts from a class-individual to its instances.

**Summary for RDF/RDFS:**

| Use case               | Result                  | Notes                                                                                   |
| ---------------------- | ----------------------- | --------------------------------------------------------------------------------------- |
| UC1: individual typing | ✓ syntactically allowed | No class/instance separation; rdfs9 propagates correctly but via undifferentiated roles |
| UC2: generic sentences | ✗ semantically broken   | rdfs2 infers wrong types on Canis_lupus; no propagation to members                      |

---

### OWL 2 DL

OWL 2 DL introduces explicit punning: `Canis_lupus` can be simultaneously a class (in the class domain ΔC) and an individual (in the individual domain ΔI). The two interpretations are semantically independent — a reasoner treats them as distinct objects that happen to share an IRI.

#### UC1 — Individual typing

```turtle
-- Class role
:Canis_lupus  rdf:type        owl:Class .
:Canis_lupus  rdfs:subClassOf :Canis .

-- Individual role
:Canis_lupus  rdf:type              :Taxon .
:Canis_lupus  :parentTaxon          :Canis .
:Canis_lupus  :conservationStatus   :LeastConcern .

-- Individual typing
:Tito  rdf:type  :Canis_lupus .
```

This is valid OWL 2 DL. `Tito rdf:type Canis_lupus` uses `Canis_lupus` in its class role; `Canis_lupus rdf:type Taxon` uses it in its individual role. No contradiction, no collapse.

Individual typing works cleanly.

#### UC2 — Generic sentences

```turtle
:Canis_lupus  :eats  :Deer .
```

In OWL 2 DL this is an ABox assertion on the _individual_ `Canis_lupus` (in ΔI). The domain inference from `:eats rdfs:domain :Animal` fires on the individual, not on the class — so the class extension (all actual wolves) is unaffected.

But the generic sentence still says nothing about individual wolves. `:Canis_lupus :eats :Deer` as an individual assertion is semantically disconnected from Tito. To propagate to members, you would need a class axiom:

```turtle
:Canis_lupus  rdfs:subClassOf  (:eats some :Deer) .
```

This is a universal restriction — every wolf eats some deer, no exceptions. Too strong for a generic sentence.

OWL 2 DL cannot express "wolves typically eat deer, with exceptions". Generic sentences fall outside its expressivity.

**Summary for OWL 2 DL:**

| Use case               | Result              | Notes                                                                            |
| ---------------------- | ------------------- | -------------------------------------------------------------------------------- |
| UC1: individual typing | ✓ fully expressible | Punning separates class and individual roles cleanly                             |
| UC2: generic sentences | ✗ not expressible   | Individual assertion disconnected from members; universal restriction too strong |

---

### SHACL

TODO

---

## Summary table

| Formalism  | UC1: individual typing                                            | UC2: generic sentences                                                  |
| ---------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------- |
| RDF / RDFS | ✓ (syntactic) — roles not separated, rdfs2 fires wrong inferences | ✗ — rdfs2 wrong type on Canis_lupus; no propagation to members          |
| OWL 2 DL   | ✓ — punning separates roles cleanly                               | ✗ — individual assertion disconnected; universal restriction too strong |
| SHACL      | TODO                                                              | TODO                                                                    |

---

## What YAGO does today

### Why UC1 fails in YAGO

Stage 02 (`make-taxonomy.py`): `wdt:P171` (parentTaxon) is an `instanceIndicator`. Any entity with P171 is excluded from the class taxonomy — it never becomes a YAGO class.

Canis lupus has `wdt:P171 Canis` → instanceIndicator fires → excluded from taxonomy → processed as a plain instance in Stage 03.

Verified from real YAGO data on the university server:

```turtle
yago:Wolf  rdf:type            schema:Taxon .
yago:Wolf  schema:parentTaxon  yago:Canis .
yago:Wolf  rdfs:label          "Canis lupus"@en .
yago:Wolf  yago:consumes       yago:Deer .
yago:Wolf  yago:consumes       yago:Reindeer .
yago:Wolf  yago:consumes       yago:Moose .
-- ... 20+ prey entries total
```

`yago:Wolf` is a plain instance of `schema:Taxon`. `?x rdf:type yago:Wolf` returns nothing.

### Why UC2 is partial in YAGO

Generic sentences survive only if the property is defined in the YAGO schema for `schema:Taxon`. `yago:consumes` (from `wdt:P1034`, predator-prey) is in the schema → survives. `eats`, `livesIn`, `conservationStatus` are not mapped → dropped.

Even the surviving `yago:consumes` facts are stored on the `yago:Wolf` instance node and are not connected to individual wolves. A query "what does Tito eat?" returns nothing, because Tito cannot be typed as `yago:Wolf`.

### Capability table

| Desired capability                          | Status in YAGO | Reason                                       |
| ------------------------------------------- | -------------- | -------------------------------------------- |
| UC1: `?x rdf:type yago:Wolf`                | ✗ impossible   | `yago:Wolf` is an instance, not a class      |
| UC1+: join individual wolf → species facts  | ✗ impossible   | depends on UC1                               |
| UC2: `yago:Wolf yago:consumes yago:Deer`    | ✓ partial      | `yago:consumes` is in schema — survives      |
| UC2: `yago:Wolf :livesIn :Forest`           | ✗ impossible   | no habitat property in YAGO schema for Taxon |
| UC2: propagate generic facts to individuals | ✗ impossible   | even with consumes, Tito cannot be typed     |

---

## Empirical tests

Test files: `tests/animals-schema.ttl`, `tests/animals-desired.ttl`, `tests/animals-yago-today.ttl`

```bash
# generate RDFS closure
riot --rdfs=tests/animals-schema.ttl tests/animals-desired.ttl > /tmp/animals-inferred.ttl
# query
arq --data=/tmp/animals-inferred.ttl --query=<queryfile>
```

### Inferred types for Canis_lupus (desired graph, RDFS closure)

```
ex:Canis_lupus  rdf:type  ex:Animal      ← inferred via rdfs2 from (eats rdfs:domain Animal)
ex:Canis_lupus  rdf:type  ex:LivingThing ← inferred via rdfs9 from (Animal subClassOf LivingThing)
ex:Canis_lupus  rdf:type  ex:Taxon       ← inferred via rdfs2 from (conservationStatus rdfs:domain Taxon)
ex:Canis_lupus  rdf:type  owl:Class      ← explicitly asserted
```

The `rdf:type ex:Animal` inference is wrong: it fires because of the generic sentence `:Canis_lupus :eats :Deer` combined with `eats rdfs:domain Animal`. RDFS conflates the class-level triple with an instance-level assertion.

### Query results: desired vs. YAGO today

| Query                             | Desired (RDFS closure)   | YAGO today    | Reason                                  |
| --------------------------------- | ------------------------ | ------------- | --------------------------------------- |
| UC2: animals that consume deer    | `Canis_lupus` ✓          | `yago:Wolf` ✓ | `yago:consumes` is in schema            |
| UC2: animals that live in forests | `Canis_lupus` ✓          | empty ✗       | no habitat property in schema           |
| UC2: conservation status          | `LeastConcern` ✓         | —             | property not mapped for Taxon           |
| UC1: individual wolves            | `Tito` ✓                 | empty ✗       | `yago:Wolf` is an instance, not a class |
| UC1+UC2: wolves + species facts   | `(Tito, LeastConcern)` ✓ | empty ✗       | depends on UC1                          |

---

## Open questions

- Could a **third role** (kind), distinct from both class and instance, solve UC2? What would its semantics be?
- Could **named graphs** separate generic triples from entity triples on the same node?
- Could **reification** of some kind (`rdf:Statement`) annotate a triple as generic vs. universal?
- Does **OWL 2 Full** (where the class/individual distinction collapses) help or make UC2 worse?
