# Use Case: Diseases

## Example: COVID-19

### The problem

In Wikidata, COVID-19 (Q84263196) carries both:

- `wdt:P279` (subclass of): _coronavirus disease_, _disease_, ...
- `wdt:P31` (instance of): _class of disease_, ...

The same entity is simultaneously used as a class (it is a type of coronavirus disease) and as an instance (it is a specific disease with an ICD code, a known pathogen, a start date).

The same pattern holds for almost all specific diseases in Wikidata:

| Disease                  | P279 (subclass of)                       | P31 (instance of)         |
| ------------------------ | ---------------------------------------- | ------------------------- |
| COVID-19                 | coronavirus disease, respiratory disease | pandemic, disease         |
| Influenza A              | influenza                                | infectious disease        |
| Diabetes mellitus type 2 | diabetes mellitus                        | disease                   |
| Alzheimer's disease      | dementia                                 | neurodegenerative disease |

This is a systematic, domain-wide punning problem.

---

### How YAGO handles it (current version, as of 2026-04-03)

`schema:MedicalEntity`, `schema:MedicalCondition`, `schema:MedicalProcedure`, and `schema:MedicalSpecialty` have all been removed from the YAGO schema

#### Step 02 (`make-taxonomy.py`)

The instanceIndicators are:

```python
instanceIndicators = {
    "wdt:P171",  # parent taxon -> instance of Taxon
    "wdt:P176",  # manufacturer -> instance of Product
    "wdt:P178",  # developer -> instance of Product
    "wdt:P580"   # start time -> instance of Event
}
```

COVID-19 has `wdt:P580` (start time), but only as a qualified statement in most Wikidata dumps, not as a direct `wdt:P580` triple. So the instanceIndicator check does not fire. The WikidataVisitor sees `wdt:P279` and adds COVID-19 to `wikidataTaxonomyDown`.

However, the taxonomy building starting from YAGO schema classes (lines 260–263 of make-taxonomy.py) finds no schema class whose `ys:fromClass` maps to any ancestor of COVID-19 in Wikidata. With `schema:MedicalCondition` removed and its `ys:fromClass wd:Q7189713` gone, the entire disease taxonomy has no anchor in YAGO. COVID-19 is never added to `yagoTaxonomyUp`.

#### Step 03 (`make-facts.py`)

COVID-19 is not in `yagoTaxonomyUp`, so `make-facts.py` tries to type it via `wdt:P31`:

```python
for obj in entityFacts.objectsOf(mainEntity, wdt:P31):
    if obj in yagoTaxonomyUp:          # only if the type is a YAGO class
        entityFacts.add((mainEntity, rdf:type, obj))
```

COVID-19's `wdt:P31` values, "disease", "public health emergency", are themselves not in `yagoTaxonomyUp` (they have no path to any remaining YAGO class). No type is assigned. COVID-19 is written to the meta file as `schema:Thing` with reason `"no valid type"`.

**COVID-19 disappears from YAGO entirely.**

---

### Comparison with other domains

|                                   | Bio-taxonomy (Canis lupus)     | Disease (COVID-19)                             |
| --------------------------------- | ------------------------------ | ---------------------------------------------- |
| Is the class role useful?         | Yes, individual wolves exist   | No, individual cases are not in YAGO           |
| Are entity-level facts important? | Yes (parentTaxon, IUCN status) | Yes (ICD code, pathogen, symptoms, start date) |
| YAGO's choice (previous)          | instance (flatten to taxon)    | class (P279 wins, MedicalCondition existed)    |
| YAGO's choice (current)           | instance (flatten to taxon)    | drop entirely (no medical class in schema)     |
| Information lost                  | cannot type individual wolves  | entity disappears; no medical facts in YAGO    |

---

### The instanceIndicator asymmetry (unchanged)

The instanceIndicator mechanism remains asymmetric across domains:

- Biological taxa are protected by `wdt:P171` → correctly typed as instances
- Products are protected by `wdt:P176` / `wdt:P178` → excluded from taxonomy (but then disappear due to P31 failure)
- Events are protected by `wdt:P580` → only for direct triples
- Diseases have no dedicated instanceIndicator → and now no YAGO class to fall into either

---

### Analysis by formalism

| Formalism | How it handles it                                                              | Pros              | Cons                                              |
| --------- | ------------------------------------------------------------------------------ | ----------------- | ------------------------------------------------- |
| RDF/RDFS  | P279 and P31 are both just triples; no mechanism to distinguish class fact from instance fact; domain/range inference fires on both equally | permissive | RDFS cannot separate "COVID-19 is a subtype of coronavirus disease" (class fact) from "COVID-19 is a disease entity" (instance fact) — both look like triples on the same subject |
| OWL 2     | explicit punning via two-domain semantics — COVID-19 as class (of cases) and individual (with ICD code, pathogen); domain inferences on entity facts do not bleed into the class extension | formally correct | requires OWL 2 DL; and the class role (typing individual cases) is semantically real but practically useless if individual cases are never represented in the KB |
| Wikidata  | both P31 and P279, no resolution                                               | pragmatic         | no single clear interpretation                    |
| SNOMED CT | diseases are concepts, not classes; subsumption is P279-like but concept-level | medically correct | complex model, not RDF-native                     |
| YAGO 4.5  | no medical class → diseases disappear from the KB                              | avoids punning    | entire medical domain absent from YAGO            |

Note: diseases are the use case where the class role is most semantically justified (individual COVID-19 cases exist and could in principle be represented), yet YAGO derives the least benefit from it. The punning cost is real, but so is the cost of opting out.

---

### Why do we need both here?

Without COVID-19 as a class:

- Cannot type individual cases as `rdf:type yago:COVID-19`
- But: individual cases are not in YAGO, so this is a theoretical loss only

Without COVID-19 as an instance:

- Cannot attach ICD code, pathogen, symptoms, start date, treatments
- This is a real, practical loss — these are the main facts one wants about a disease

**Verdict**: the current YAGO design opts out of the medical domain entirely. This avoids the punning problem but at the cost of all medical knowledge. An alternative would be to add a disease-specific instanceIndicator (e.g., `wdt:P557` ICD code, or `wdt:P780` symptoms) and a lightweight `schema:MedicalCondition` class, this would let diseases be typed as instances with their entity facts, at the cost of accepting that the "class of cases" reading is lost.

---

## Questions

- [ ] What would it take to reintroduce `schema:MedicalCondition` with a minimal property set (ICD code, pathogen) and an instanceIndicator on `wdt:P557`?
- [ ] How does SNOMED CT's concept model compare to the YAGO class/instance choice?
- [ ] Compare Wikidata vs. MeSH treatment of disease classification —> does MeSH encode diseases as instances or classes?
