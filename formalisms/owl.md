# Formalism: OWL 2

## What OWL 2 is

OWL 2 (Web Ontology Language, version 2) extends RDFS with a richer vocabulary for expressing class axioms, property constraints, and individual assertions. It is grounded in Description Logic (specifically SROIQ(D)), which gives it a formal model-theoretic semantics and decidable reasoning.

OWL 2 has several profiles (EL, QL, RL, DL, Full) with different expressivity/decidability trade-offs. The relevant one for punning is **OWL 2 DL** (Description Logic).

---

## Punning in OWL 2 DL: explicit support

OWL 2 DL explicitly allows an IRI to denote both a class and an individual. This is called punning in the OWL 2 specification, and it is a deliberate design decision.

```turtle
# Dog as a class
ex:Dog  rdf:type          owl:Class .
ex:Dog  rdfs:subClassOf   ex:Animal .

# Dog as an individual
ex:Dog  rdf:type          ex:DomesticSpecies .
ex:Dog  ex:domesticatedBy ex:Humans .
```

Both are valid in OWL 2 DL. The same IRI `ex:Dog` is simultaneously a class (in the TBox) and an individual (in the ABox).

---

## How OWL 2 DL interprets punning: separate metalevel

The key in OWL 2 punning is the two-domain semantics. OWL 2 DL models have two separate domains:

- **ΔI** — the domain of individuals (ABox)
- **ΔC** — the domain of classes (TBox, which is the powerset of ΔI)

When an IRI is used as both a class and an individual, OWL 2 DL interprets them as two different entities: one in ΔC (the class extension) and one in ΔI (the individual). The IRI is shared syntactically but the two entities are not required to be related semantically.

```
ex:Dog (as class)      →  extension = { Rex, Tito, Lassie, ... } ⊆ ΔI
ex:Dog (as individual) →  some element d ∈ ΔI
```

These two interpretations are independent. There is no built-in relationship between "the class Dog" and "the individual Dog". In particular:

- `ex:Rex rdf:type ex:Dog` does NOT entail that the individual ex:Dog has any relation to ex:Rex
- `ex:Dog ex:domesticatedBy ex:Humans` does NOT say anything about the members of the Dog class

This is safe punning: the two roles never interact under the OWL 2 DL semantics.

---

## Contrast with RDFS: why OWL is safer

In RDFS, the domain/range inference rules operate on all triples regardless of whether the subject is being used as a class or an individual (see `rdf.md`). OWL 2 DL avoids this by:

1. Separating the class domain from the individual domain at the semantic level
2. Restricting which axioms can appear in each context (class axioms vs. individual assertions)
3. Making the two uses of the same IRI semantically independent

In RDFS:

```turtle
ex:eats  rdfs:domain  ex:Animal .
ex:Dog   ex:eats      ex:Bones .
# RDFS infers: ex:Dog rdf:type ex:Animal  ← unintended
```

In OWL 2 DL:

```turtle
ex:eats  rdfs:domain  ex:Animal .
ex:Dog   ex:eats      ex:Bones .   # ex:Dog used as individual
# OWL 2 infers: ex:Dog (individual) rdf:type ex:Animal  ← isolated to the individual
# ex:Dog (class) is unaffected
```

The inference is contained to the individual interpretation of ex:Dog, not the class interpretation.

---

## OWL 2 Full vs. OWL 2 DL on punning

**OWL 2 Full** merges the class and individual domains completely. a class IS a set of individuals, and a class can be used as an individual directly. This is mathematically elegant but makes reasoning undecidable (equivalent to second-order logic). For what i learned most OWL tooling does not support OWL 2 Full.

**OWL 2 DL** (the practically used profile) keeps the two domains separate via the punning mechanism, achieving decidability at the cost of the semantic independence described above. Punning in OWL 2 DL is a syntactic convenience, not a deep semantic claim.

---

## What OWL 2 can express about the punning cases

### Biological taxonomy (Canis lupus)

```turtle
# Class role: Canis lupus as a class of individual wolves
ex:Canis_lupus  rdf:type          owl:Class .
ex:Canis_lupus  rdfs:subClassOf   ex:Canis .
ex:Tito         rdf:type          ex:Canis_lupus .   # individual wolf

# Individual role: Canis lupus as an entity with facts
ex:Canis_lupus  rdf:type          ex:Taxon .         # punning
ex:Canis_lupus  ex:parentTaxon    ex:Canis .
ex:Canis_lupus  ex:conservationStatus  ex:LeastConcern .
```

OWL 2 DL allows this. The class axiom (`rdfs:subClassOf`) and the individual assertion (`ex:parentTaxon`) are interpreted in separate domains and do not interfere.

**What OWL 2 cannot express**: the generic sentence problem. `ex:Canis_lupus ex:eats ex:Deer` (wolves eat deer) is either:

- An individual assertion on the Canis_lupus individual (does not say anything about actual wolves)
- A universal restriction on the class: `rdfs:subClassOf (ex:eats some ex:Deer)` (too strong: requires every wolf to eat deer)

There is no standard OWL construct for "wolves-as-a-kind typically eat deer, with exceptions". Generic sentences are outside the OWL 2 expressivity.

### Diseases (COVID-19)

```turtle
# Class role: every COVID-19 case is an instance of this class
ex:COVID-19  rdf:type          owl:Class .
ex:COVID-19  rdfs:subClassOf   ex:CoronavirusDisease .

# Individual role: COVID-19 as an entity with facts
ex:COVID-19  rdf:type          ex:Disease .           # punning
ex:COVID-19  ex:causedBy       ex:SARS-CoV-2 .
ex:COVID-19  ex:icdCode        "RA01.0" .
```

OWL 2 DL allows this. The class role (for typing individual cases) and the individual role (for the ICD code, pathogen) coexist under the two-domain semantics.

---

## The limits of OWL 2 punning

### 1. No semantic connection between the two roles

The class Dog and the individual Dog are not connected by OWL semantics. You cannot express:

- "The individual Dog represents the extension of the class Dog"
- "Properties of the class (size of the class, typical member properties) are linked to the individual"

The two interpretations are semantically independent. This is exactly why generic sentences cannot be expressed.

### 2. Tooling support is incomplete

Most OWL 2 DL reasoners (HermiT, Pellet, ELK) handle punning correctly, but:

- Some serializations (RDF/XML) do not distinguish the two uses of the same IRI syntactically
- Some tools conflate the class and individual interpretations
- SPARQL queries over OWL ontologies often do not distinguish the TBox from the ABox

### 3. Decidability cost

OWL 2 DL is decidable but high-complexity. In practice, large KBs cannot use full OWL 2 DL reasoning.

---

## OWL 2 and YAGO

YAGO uses OWL only minimally:

```turtle
schema:Person  owl:disjointWith  schema:Organization .
yago:Elvis     owl:sameAs        wd:Q_Elvis .
```

YAGO does NOT use OWL 2 punning. Instead, it resolves the class/instance ambiguity at ingestion time (step 02) by forcing a binary choice. The reasons are practical:

1. YAGO is designed to work with SPARQL and SHACL, not with OWL reasoners
2. OWL 2 punning's semantic independence means the two roles cannot be linked — which is exactly the information YAGO would want to preserve
3. The two-domain interpretation would make SHACL validation ambiguous (which domain does a NodeShape apply to?)

---

## Summary

| Aspect                        | OWL 2 DL behavior                                                |
| ----------------------------- | ---------------------------------------------------------------- |
| Punning allowed?              | Yes — explicitly supported as a language feature                 |
| Semantics of punning          | Two-domain: class and individual interpretations are independent |
| Inference risk (domain/range) | Contained — inferences on the individual do not affect the class |
| Generic sentences             | Not expressible — universal restrictions are too strong          |
| Tooling support               | Partial — reasoners handle it, SPARQL/SHACL less so              |
| Decidability                  | Yes (OWL 2 DL) — but high complexity                             |
| Used in YAGO?                 | Only for `owl:disjointWith` and `owl:sameAs`, not for punning    |
