# Use Case: Chemical Substances

## Examples: H₂O (water), Aspirin

## The two use cases

### UC1 — Taxonomy node with entity-level facts

Chemical substances sit in a deep taxonomy (H₂O is a subclass of oxide, of hydrogen compound, of inorganic compound, of chemical compound). At the same time, each substance carries entity-level facts that are specific to it as a named entity:

```turtle
:H2O  rdfs:subClassOf  :Oxide .
:H2O  rdfs:subClassOf  :HydrogenCompound .

:H2O  :molecularFormula  "H2O" .
:H2O  :boilingPoint      "100"^^xsd:decimal .
:H2O  :molarMass         "18.015"^^xsd:decimal .
:H2O  :CASNumber         "7732-18-5" .
```

These two requirements conflict: if `:H2O` is a class node in the taxonomy, any formalism that separates classes from instances prevents it from carrying instance-level properties. We lose the molecular data.

### UC2 — Drug as active ingredient (pharmacological links)

Aspirin sits in the chemical/pharmacological taxonomy as a subclass of NSAID and analgesic. At the same time, we want to express pharmacological facts about it as a named entity:

```turtle
:Aspirin  rdfs:subClassOf  :NSAID .
:Aspirin  rdfs:subClassOf  :Analgesic .

:Aspirin  :mechanismOfAction  :COX_inhibitor .
:Aspirin  :treats             :Headache .
:Aspirin  :treats             :Fever .
:Aspirin  :contraindication   :PepticUlcer .
:Aspirin  :CASNumber          "50-78-2" .
```

The critical punning tension appears in links from other entities:

```turtle
:Prescription_42  :prescribes   :Aspirin .   # Aspirin as instance
:PatientRecord_7  :intolerantTo :Aspirin .   # Aspirin as instance
```

For `:prescribes` and `:intolerantTo` to work, `:Aspirin` must be typed as an instance (so the domain/range checks pass). But for `:Aspirin rdfs:subClassOf :NSAID` to hold, it must be a class. The same node must play both roles simultaneously.

`:Aspirin :treats :Headache` is also a generic sentence — not every use of aspirin treats a headache — which compounds the problem beyond the class/instance conflict.

### UC3 — ATC pharmaceutical classification codes

The ATC classification system (Anatomical Therapeutic Chemical) organizes drugs into a five-level hierarchy. Each level node is simultaneously an instance of the classification system and a class whose instances are the next-level codes:

```turtle
:ATC_A  rdf:type         :ATCClassification .  # instance of the system
:ATC_A  :atcCode         "A" .
:ATC_A  :description     "Alimentary tract and metabolism" .

:ATC_A01  rdf:type    :ATC_A .               # instance of ATC_A
:ATC_A01  :atcCode    "A01" .
:ATC_A01  :description "Stomatological preparations" .

:ATC_A01A  rdf:type   :ATC_A01 .             # instance of ATC_A01
```

`:ATC_A` must be both a class (so that `:ATC_A01 rdf:type :ATC_A` holds) and an instance (so that it carries its own code and description as facts). This is confirmed by Wikidata data: ATC code A, D, J all appear as punning entities (P31 ∩ P279 = ATCClassification).

Unlike the other use cases, the punning here is **intentional and structural** — the classification system is designed so that every internal node is both a named entity and a classifier for the level below. This makes it a clean test case: the punning cannot be resolved by "flattening" the hierarchy.

---

## The punning structure

H₂O in Wikidata has both:

- `wdt:P279` (subclass of): chemical compound, oxide, hydrogen compound, inorganic compound
- `wdt:P31` (instance of): type of chemical entity, chemical substance

The same entity must be:

- a **class node** in the chemical taxonomy (so the subclass chain is preserved and substance samples can be typed)
- an **instance** carrying entity-level facts (molecular formula, boiling point, CAS number)

This pattern is systematic across chemical domains:

| Substance | P279 (subclass of)            | Entity facts wanted                                       |
| --------- | ----------------------------- | --------------------------------------------------------- |
| H₂O       | oxide, hydrogen compound      | molecular formula, boiling point, molar mass, CAS number  |
| Aspirin   | analgesic, NSAID              | IUPAC name, molecular formula, CAS number, molar mass     |
| Ethanol   | alcohol, organic solvent      | molecular formula, boiling point, flash point, CAS number |
| NaCl      | ionic compound, chloride salt | solubility, melting point, CAS number                     |

---

## Desired facts and queries

```turtle
# UC1 — entity-level facts on a taxonomy node
:H2O  :molecularFormula  "H2O" .
:H2O  :boilingPoint      "100"^^xsd:decimal .
:H2O  :molarMass         "18.015"^^xsd:decimal .
:H2O  :CASNumber         "7732-18-5" .
:MyBottle  :contains  :H2O .

# UC2 — pharmacological links require Aspirin as instance
:Aspirin  :mechanismOfAction  :COX_inhibitor .
:Aspirin  :treats             :Headache .
:Prescription_42  :prescribes :Aspirin .

# UC3 — ATC hierarchy: each node is both instance and class
:ATC_A    rdf:type  :ATCClassification .
:ATC_A    :atcCode  "A" .
:ATC_A01  rdf:type  :ATC_A .
:ATC_A01  :atcCode  "A01" .
```

```sparql
# "What is the CAS number of water?"
SELECT ?cas WHERE { :H2O :CASNumber ?cas }
# Today: returns empty — entity facts dropped in stage 03

# "What drugs treat headache?"
SELECT ?drug WHERE { ?drug :treats :Headache }
# Today: broken — :Aspirin is a class, no entity facts survive

# "Find all drugs prescribed in prescription 42"
SELECT ?drug WHERE { :Prescription_42 :prescribes ?drug }
# Today: broken — domain/range check fails, Aspirin is not a typed instance

# "What is ATC code A?"
SELECT ?desc WHERE { :ATC_A :description ?desc }
# Today: returns empty — ATC_A is processed as a class, facts dropped
```

---

## Analysis by formalism

### RDF / RDFS

#### UC1 — Taxonomy node with entity-level facts

RDF has no class/instance barrier. Both roles coexist without contradiction:

```turtle
:H2O  rdfs:subClassOf    :Oxide .
:H2O  :molecularFormula  "H2O" .
:H2O  :boilingPoint      "100"^^xsd:decimal .
```

If `boilingPoint rdfs:domain ChemicalSubstance`, rdfs2 infers `:H2O rdf:type ChemicalSubstance` — correct.

#### UC2 — Drug as active ingredient

`:Aspirin :treats :Headache` is writable. If `treats rdfs:domain Drug`, rdfs2 infers `:Aspirin rdf:type Drug` — correct. `:Prescription_42 :prescribes :Aspirin` is also syntactically valid; no range check enforced by RDFS alone. The generic sentence problem remains: `:Aspirin :treats :Headache` says nothing about individual administrations.

#### UC3 — ATC classification

`:ATC_A rdf:type :ATCClassification` and `:ATC_A01 rdf:type :ATC_A` are both valid in RDF. Both roles on `:ATC_A` coexist. No barrier.

**Summary for RDF/RDFS:**

| Use case                         | Result            | Notes                                          |
| -------------------------------- | ----------------- | ---------------------------------------------- |
| UC1: taxonomy + entity facts     | ✓ coexist         | No class/instance barrier                      |
| UC2: drug as active ingredient   | ✓ coexist         | Generic sentence problem remains               |
| UC3: ATC classification          | ✓ coexist         | Multi-level hierarchy fully expressible        |

---

### OWL 2 DL

#### UC1 — Taxonomy node with entity-level facts

OWL 2 DL punning separates the class role (ΔC) and the individual role (ΔI):

```turtle
:H2O  rdf:type        owl:Class .
:H2O  rdfs:subClassOf :Oxide .          # class role
:H2O  rdf:type        :ChemicalSubstance .
:H2O  :molecularFormula "H2O" .         # individual role
:H2O  :boilingPoint   "100"^^xsd:decimal .
```

Entity facts on the individual do not bleed into the class extension. Both requirements satisfied.

#### UC2 — Drug as active ingredient

```turtle
:Aspirin  rdf:type    owl:Class .
:Aspirin  rdfs:subClassOf :NSAID .       # class role

:Aspirin  rdf:type    :Drug .
:Aspirin  :treats     :Headache .        # individual role
:Prescription_42  :prescribes  :Aspirin .
```

OWL 2 DL punning allows this. `:prescribes` can have range `:Drug` and `:Aspirin` satisfies it as an individual. The generic sentence `:Aspirin :treats :Headache` remains unresolved — it lives on the individual, says nothing about specific administrations.

#### UC3 — ATC classification

Each ATC node is an individual *and* a class. In OWL 2 DL:

```turtle
:ATC_A   rdf:type  owl:Class .
:ATC_A   rdf:type  :ATCClassification .   # individual role
:ATC_A   :atcCode  "A" .

:ATC_A01  rdf:type  :ATC_A .              # uses ATC_A as class
:ATC_A01  rdf:type  owl:Class .
:ATC_A01  :atcCode  "A01" .
```

Valid OWL 2 DL punning. The full five-level hierarchy is expressible. Each node carries its own facts and can be used as a classifier for the next level.

**Summary for OWL 2 DL:**

| Use case                       | Result              | Notes                                                          |
| ------------------------------ | ------------------- | -------------------------------------------------------------- |
| UC1: taxonomy + entity facts   | ✓ fully expressible | Punning separates roles cleanly                                |
| UC2: drug as active ingredient | ✓ fully expressible | Generic sentence not resolved; prescribes link works           |
| UC3: ATC classification        | ✓ fully expressible | Multi-level punning valid; each node plays both roles          |

---

### SHACL

TODO

---

## Summary table

| Formalism  | UC1: taxonomy + entity facts  | UC2: drug as active ingredient                      | UC3: ATC classification             |
| ---------- | ----------------------------- | --------------------------------------------------- | ----------------------------------- |
| RDF / RDFS | ✓ — no class/instance barrier | ✓ — coexist; generic sentence unresolved            | ✓ — multi-level hierarchy valid     |
| OWL 2 DL   | ✓ — punning separates roles   | ✓ — prescribes link works; generic sentence remains | ✓ — each node plays both roles      |
| SHACL      | TODO                          | TODO                                                | TODO                                |

---

## What YAGO does today

### How H₂O is processed

Stage 02 (`make-taxonomy.py`): H₂O has `wdt:P279` → added to `wikidataTaxonomyDown`. No
instanceIndicator fires (there is no property analogous to P171 for chemical substances in the
YAGO configuration). H₂O enters the taxonomy as a class node.

Stage 03 (`make-facts.py`): H₂O is in the taxonomy → assigned `rdf:type rdfs:Class` → all
entity-level facts fail the domain check and are dropped. There is no `schema:ChemicalSubstance`
class in the YAGO 4.5 schema, so H₂O receives no type assignment and no properties survive.

Stage 04 (`make-facts.py` domain check): if a property like `:contains` expects a
`schema:ChemicalSubstance` in its range, and `:H2O` is a class (not a typed instance), the link
`:MyBottle :contains :H2O` fails or is dropped.

### Capability table

| Desired capability                                     | Status in YAGO | Reason                              |
| ------------------------------------------------------ | -------------- | ----------------------------------- |
| Taxonomy: `yago:H2O rdfs:subClassOf yago:Oxide`        | ✓ preserved    | P279 survives in taxonomy           |
| Entity: `yago:H2O :molecularFormula "H2O"`             | ✗ dropped      | processed as class; no entity facts |
| Entity: `yago:H2O :boilingPoint "100"`                 | ✗ dropped      | same reason                         |
| Entity: `yago:H2O :CASNumber "7732-18-5"`              | ✗ dropped      | same reason                         |
| Link: `:MyBottle :contains yago:H2O`                   | ✗ broken       | domain/range check fails            |
| Drug: `yago:Aspirin :treats yago:Headache`             | ✗ dropped      | Aspirin is a class; no entity facts |
| Link: `:Prescription :prescribes yago:Aspirin`         | ✗ broken       | domain/range check fails            |
| ATC entity: `yago:ATC_A :atcCode "A"`                  | ✗ dropped      | ATC_A processed as class            |
| ATC typing: `:ATC_A01 rdf:type yago:ATC_A`             | ✗ impossible   | ATC_A has no rdf:type in YAGO schema|

**Note**: unlike diseases, which at least preserve the taxonomy meaningfully (disease hierarchy is
useful for queries), the chemical taxonomy in YAGO is navigable but entirely content-free — no
molecular data, no physical properties, no CAS codes.

### Comparison with diseases and animals

| Domain         | instanceIndicator | YAGO result                 | What is lost            |
| -------------- | ----------------- | --------------------------- | ----------------------- |
| Animals (taxa) | P171 → instance   | entity survives as instance | individual typing (UC2) |
| Diseases       | none → class      | taxonomy preserved          | all entity facts (UC1)  |
| Chemicals      | none → class      | taxonomy preserved          | all entity facts (UC1)  |

Chemicals and diseases share the same failure mode in YAGO. The difference is semantic: disease
entity facts (ICD code, pathogen) are important for medical queries; chemical entity facts
(molecular formula, boiling point) are important for scientific queries. Both are dropped.

---

## Open questions

- Would adding an `instanceIndicator` on a chemical property (e.g. `wdt:P231`, CAS registry number) solve UC1 — at the cost of breaking the taxonomy (same trade-off as taxa)?
- How does ChEBI (Chemical Entities of Biological Interest) handle the class/instance distinction for chemical substances?
- Are there chemical substances in YAGO that currently survive as instances (i.e., that have an instanceIndicator)?
