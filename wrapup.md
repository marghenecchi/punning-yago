# Wrap-up :)

---

## What was done this week

### 1. Understanding how YAGO handles punning today (`notes/general-analysis.md`)

Traced the three pipeline stages that resolve punning:

- **Stage 02 (`make-taxonomy.py`)**: an entity becomes a class if it has `wdt:P279` and none of the `instanceIndicators` (`P171` parent taxon, `P176` manufacturer, `P178` developer, `P580` start time). If both conditions fire, the instance indicator wins and the entity is excluded from the taxonomy.
- **Stage 03 (`make-facts.py`)**: if an entity is in the taxonomy, it gets `rdf:type rdfs:Class` and all entity-level facts are dropped via a domain check. If it is not in the taxonomy, it must be typed via `wdt:P31`; if no valid type is found, it is written to the meta file as `schema:Thing` and disappears from the main KB.
- **Stage 04 (`make-typecheck.py`)**: if a property expects an instance of class C but the object is a class (subclass of C), YAGO substitutes a blank node `_:ClassName_generic_instance`. The direct link to the entity is broken.

---

### 2. Formalism analysis (`formalisms/`)

Two formalisms analized:

**RDF/RDFS (`rdf.md`)**

- Punning is the default: no mechanism prevents an IRI from being both a class and an instance.
- The RDFS metalevel (`rdfs:Class`) is itself a canonical form of punning.
- Core problem: domain/range rules (rdfs2, rdfs3) fire on class-level triples, causing unintended type inferences (e.g., `Dog eats Bones` + `eats rdfs:domain Animal` → `Dog rdf:type Animal`, even if Dog was meant as a class).
- No way to distinguish "fact about the kind" from "fact about the individual" within the RDF data model.

**OWL 2 DL (`owl.md`)**

- Punning is explicitly supported: an IRI can denote a class (in ΔC) and an individual (in ΔI) simultaneously. The two interpretations are semantically independent.
- Domain/range inferences are isolated to the individual interpretation, they do not bleed into the class extension.
- Key limitation: the two roles are not semantically connected. No OWL construct can express "the individual Dog represents the extension of the class Dog".
- Generic sentences (wolves eat deer, true of the kind but not of every individual) remain inexpressible. Universal restrictions are too strong and do not allow exceptions.
- Not used in YAGO for punning: YAGO uses OWL only for `owl:disjointWith` and `owl:sameAs`.

---

### 3. Use case analysis (`use-cases/`)

Five (for now) use cases documented. Each one exposes a different failure mode of YAGO's binary model.

#### Animals / Biological taxonomy (`animals.md`), example used: Canis lupus

YAGO's solution: flatten all taxa to instances. The hierarchy is preserved via `schema:parentTaxon` (a regular property, not `rdfs:subClassOf`).

What is lost: individual animals cannot be typed (`Tito rdf:type Canis_lupus` is impossible because Canis lupus is not a class).

Deeper problem: the Canis lupus instance conflates two roles — the taxonomic entity (parentTaxon, IUCN status) and the natural kind for generic predications (eats deer, lives in packs). These are stored as indistinguishable triples on the same node. No formalism currently solves the generic sentence problem.

#### Diseases (`diseases.md`), example used: COVID-19

`schema:MedicalCondition` has been removed from the YAGO schema. As a result:

- COVID-19 has `wdt:P279` (subclass of coronavirus disease) but no instanceIndicator fires.
- Its P279 chain finds a path into `yagoTaxonomyUp` via `yago:Coronavirus_diseases`.
- In step 03 it gets `rdf:type rdfs:Class` and all entity-level facts (ICD code, pathogen, start date) are dropped.
- COVID-19 survives as a class (`rdfs:subClassOf yago:Coronavirus_diseases`), not as an entity with facts. All entity-level data (ICD code, pathogen, start date) are dropped.
- Step 04 detects that `yago:deathCause` expects an instance but `yago:COVID-19` is a class → creates `yago:COVID-19_generic_instance`. Every person in YAGO who died of COVID-19 has `yago:deathCause yago:COVID-19_generic_instance` instead of a direct link. The query `?person yago:deathCause yago:COVID-19` returns nothing.

Verdict: YAGO preserves the disease taxonomy but loses all entity-level medical data and breaks cause-of-death queries. A possible fix: add `wdt:P557` (ICD code) as an instanceIndicator so diseases are treated as instances with their entity facts preserved.

#### Products (`products.md`) — example: iPhone 13

Both iPhone (`yago:Smartphone_Model_Series`) and iPhone 13 (`yago:Smartphone_Model`) survive as instances with full entity facts (manufacturer, price, dimensions, release date). The instanceIndicator (`wdt:P176`) fires correctly and P31 typing succeeds because `yago:Smartphone_Model` and `yago:Smartphone_Model_Series` are valid YAGO classes.

#### Chemical substances (`chemicals.md`) — example: H₂O, aspirin

The same mechanism as diseases, applied to chemistry:

- Specific chemicals have `wdt:P279` but no instanceIndicator.
- They are added to the YAGO taxonomy as classes in step 02.
- In step 03, `rdf:type rdfs:Class` is assigned and entity-level facts (molecular formula, boiling point, CAS number, density) are dropped by the domain check.

What survives: the taxonomy structure only (rdfs:subClassOf chains). What is lost: all chemical data.

The class role is useless (individual molecules are never in YAGO). Fix: add chemical-specific instanceIndicators (`wdt:P231` CAS number, `wdt:P274` molecular formula). P31 for specific chemicals points to "chemical compound" (Q11173) which is in `yagoTaxonomyUp` → typing would succeed and facts would be preserved.

#### Languages (`languages.md`) — example: Italian

Languages have no instanceIndicators, so the entire language taxonomy ends up as classes in YAGO.

Unique failure mode: the primary loss is not entity facts (the YAGO schema defines no properties for `schema:Language`) but reference integrity. Languages are the range of `schema:inLanguage`, `yago:officialLanguage`, `schema:knowsLanguage`. Step 04 detects that a class is used where an instance is expected and substitutes a blank node `_:Italian_generic_instance`.

Result: "which books are written in Italian?" returns results pointing to an anonymous blank node, not to `yago:Italian`. Cross-fact joins over languages are broken. The blank node is YAGO's ad hoc substitute for OWL 2's individual role — it creates a temporary referent but lacks stable IRI identity.

---

## Recurring patterns across use cases

| Pattern                          | Use cases            | Root cause                                                  |
| -------------------------------- | -------------------- | ----------------------------------------------------------- |
| Entity disappears entirely       | Diseases, Products   | No YAGO class for the domain OR P31 → second-order class    |
| Entity survives as empty class   | Chemicals, Languages | P279 wins, no instanceIndicator, entity facts dropped       |
| Hierarchy flattened to instances | Animals              | Intentional: dedicated instanceIndicator (P171)             |
| Generic instance substitution    | Languages            | Class used as range value, step 04 replaces with blank node |
| Genre/typing infrastructure dead | Genres               | No `ys:fromClass` anchor for the domain class               |

**The instanceIndicator mechanism** is the key lever: only domains with a dedicated indicator (animals via P171, products via P176/P178) are consistently handled. All other domains fall through to the P279 → class path, losing their entity-level data.
