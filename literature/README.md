# Literature

## Reading list

| Title                                                     | Authors                             | Year | File                                                                             | Status |
| --------------------------------------------------------- | ----------------------------------- | ---- | -------------------------------------------------------------------------------- | ------ |
| Reasoning with Individuals for the Description Logic SHIQ | Horrocks, Sattler, Tobies           | 2000 | [Tbox.pdf](Tbox.pdf)                                                             | read   |
| OWL 2 Web Ontology Language Direct Semantics              | Motik, Patel-Schneider, Cuenca Grau | 2012 | [REC-owl2-direct-semantics-20121211.pdf](REC-owl2-direct-semantics-20121211.pdf) | read   |
| OWL 2 Structural Specification                            | W3C                                 | 2012 | —                                                                                | todo   |

---

## Paper notes

### Reasoning with Individuals for the Description Logic SHIQ

- **Authors**: Ian Horrocks, Ulrike Sattler, Stephan Tobies
- **Year**: 2000
- **Venue**: CADE-17, LNAI 1831

#### What it does

Presents a tableau algorithm for combined TBox + ABox reasoning in the SHIQ description logic. Before this work, most reasoners only handled TBox reasoning (empty ABox assumed).

#### Core concepts

A DL knowledge base has two strictly separate parts:

- **TBox** (terminological box): facts about _classes_ and _roles_ — `Man ⊑ Animal`, inclusion axioms
- **ABox** (assertional box): facts about _individuals_ — `Aristotle : Man`, `(Aristotle, Plato) : Pupil-of`

SHIQ = ALC + transitive roles (S) + inverse roles (I) + role hierarchies (H) + qualifying number restrictions (Q).

An interpretation maps every concept to a subset of the domain ΔI and every individual to an element of ΔI. The two are formally separate.

#### Relevance to the project

- Provides the formal vocabulary for what YAGO does: stage 03 assigns every entity exclusively to the TBox (class) or ABox (individual) — exactly the SHIQ separation
- The `Man ⊑ Animal` (TBox) vs `Aristotle : Man` (ABox) distinction is the template for explaining why `Canis lupus eats deer` is problematic: it is an ABox-style fact written on a TBox entity
- The paper explicitly notes that most applications use TBox-only reasoning, this kind of motivates why YAGO makes the binary choice it makes

#### Relevance to the project in the future

- The tableau algorithm is the foundation of OWL reasoners (FaCT, HermiT); useful if evaluating whether a proposed solution is decidable
- If proposing a solution based on more expressive logics, this is the formal starting point

---

### OWL 2 Web Ontology Language Direct Semantics (Second Edition)

- **Authors**: Boris Motik, Peter F. Patel-Schneider, Bernardo Cuenca Grau
- **Year**: 2012
- **Venue**: W3C Recommendation

#### What it does

Defines the formal model-theoretic semantics of OWL 2, corresponding to the description logic SROIQ (SHIQ + reflexive roles + nominals + disjoint roles).

#### Core concepts

An OWL 2 interpretation is `I = (ΔI, ΔD, ·C, ·OP, ·DP, ·I, ...)` where:

- `ΔI` = object domain
- `·C` maps each class name to a subset of `ΔI`
- `·I` maps each individual name to an element of `ΔI`

Classes and individuals share the same domain `ΔI` but are addressed by different interpretation functions.

**Key note on punning**: _"SROIQ does not provide for datatypes and punning, the semantics of OWL 2 is defined directly on the structural specification."_ Punning is NOT in the direct semantics, it is handled in the structural specification separately. When punning is used in OWL 2, the reasoner treats the class name and the individual name as **distinct entities** sharing the same IRI. There is no semantic interaction between them.

**Key note on universal restrictions**: `ObjectAllValuesFrom(OPE CE)` = `{x | ∀y: (x,y) ∈ OPE → y ∈ CE}` — this is exactly why OWL 2 is too strong for generic statements: it has no exceptions. `Wolf eats Deer` in OWL 2 means _every_ wolf eats _some_ deer, with no room for "my wolf doesn't".

**Disjointness**: `DisjointClasses(CE1 ... CEn)` means `(CEj)^C ∩ (CEk)^C = ∅` — the disjointness constraints in YAGO's schema are exactly this.

#### Relevance to the projec

- Clarifies that OWL 2 does not resolve punning semantically: it ignores it in the direct semantics and only permits it syntactically in the structural specification
- Confirms that universal restrictions (`∀`) are too strong for generic statements, no exceptions allowed
- YAGO's `owl:disjointWith` is formally `DisjointClasses` from this spec

#### Relevance to the project in th future

- If proposing a YAGO solution based on OWL 2, the structural specification (separate W3C document) is what defines how punning actually works syntactically (todo read that next)
- Section 2.5 (inference problems: consistency, entailment, satisfiability) defines the metrics for evaluating whether a proposed solution is decidable and at what computational cost

---

## Topics still to cover

- [ ] Punning in OWL 2 structural specification (the part this semantics doc explicitly defers to)
- [ ] Wikidata P31 vs P279 inconsistency, primary source of punning in YAGO
- [ ] Generic sentences / kind predication in KR (Carlson & Pelletier; defeasible DL)
- [ ] Typicality-based description logics, DL with exceptions
