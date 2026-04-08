# Use Case: Diseases

## Example: COVID-19

### The problem

In Wikidata, COVID-19 (Q84263196) carries both:

- `wdt:P279` (subclass of): _coronavirus disease_, _respiratory disease_, _infectious disease_
- `wdt:P31` (instance of): _pandemic_, _disease_, _public health emergency of international concern_

This is classic punning: the same entity is simultaneously used as a class (it is a type of coronavirus disease) and as an instance (it is a specific disease with an ICD code, a known pathogen, a start date).

The same pattern holds for almost all specific diseases in Wikidata:

| Disease                  | P279 (subclass of)                       | P31 (instance of)         |
| ------------------------ | ---------------------------------------- | ------------------------- |
| COVID-19                 | coronavirus disease, respiratory disease | pandemic, disease         |
| Influenza A              | influenza                                | infectious disease        |
| Diabetes mellitus type 2 | diabetes mellitus                        | disease                   |
| Alzheimer's disease      | dementia                                 | neurodegenerative disease |

This is a systematic, domain-wide punning problem, not a quirk of COVID-19.

---

### How YAGO handles it

#### Step 02 (`make-taxonomy.py`)

An entity becomes a YAGO class if it has `wdt:P279` (subclass of) and none of the `instanceIndicators`:

```python
instanceIndicators = {
    "wdt:P171",  # parent taxon -> instance of Taxon
    "wdt:P176",  # manufacturer -> instance of Product
    "wdt:P178",  # developer -> instance of Product
    "wdt:P580"   # start time -> instance of Event
}
```

COVID-19 has `wdt:P580` (start time: December 2019) in Wikidata. If this appears as a direct property (`wdt:P580`) in the Wikidata dump, the instanceIndicator check catches it and COVID-19 is excluded from the class taxonomy.

However, if `wdt:P580` only appears as a qualified statement (via `p:P580` on a statement node, not as a direct `wdt:P580`), the check does not fire, and COVID-19 ends up in the YAGO taxonomy as a class.

#### Step 03 (`make-facts.py`)

When an entity is in `yagoTaxonomyUp` (i.e., it became a class in step 02), the code does:

```python
if mainEntity in yagoTaxonomyUp:
    entityFacts.add((mainEntity, Prefixes.rdfType, Prefixes.rdfsClass))
    return declaredWikidataTypes  # returns immediately
```

Then `handleDomain` runs with `fullTransitiveClasses = {"rdfs:Class"}`. The domain of all medical properties is `schema:MedicalEntity`, not `rdfs:Class`. Domain check fails for every property.

**All entity-level facts of COVID-19 are removed.**

What YAGO keeps:

```turtle
yago:COVID-19  rdf:type         rdfs:Class .
yago:COVID-19  rdfs:subClassOf  schema:MedicalEntity .
yago:COVID-19  rdfs:label       "COVID-19"@en .
```

What is lost:

```turtle
yago:COVID-19  yago:causedBy    yago:SARS-CoV-2 .
yago:COVID-19  yago:symptom     yago:Fever, yago:Cough, ... .
yago:COVID-19  schema:startDate "2019-12"^^xsd:gYearMonth .
yago:COVID-19  yago:icdCode     "RA01.0" .
yago:COVID-19  schema:location  yago:Wuhan .
yago:COVID-19  yago:treatment   yago:Paxlovid, yago:mRNA_vaccine, ... .
```

---

### Why this is wrong

The class role of COVID-19 in YAGO is useless:

- Individual clinical cases are not represented in YAGO, there is no entity that would become `rdf:type yago:COVID-19`
- The `rdfs:subClassOf schema:MedicalEntity` relationship adds no queryable information that was not already present in the entity-level facts

The instance role of COVID-19 is essential:

- ICD-11 code identifies the disease in clinical systems
- The causative agent (SARS-CoV-2) is a well-defined biochemical entity
- Symptoms, treatments, start date, and geographic origin are all important facts

The `wdt:P279` in Wikidata is better read as: "every case of COVID-19 is a case of coronavirus disease" — a taxonomic IS-A relationship. But this should be modeled as:

```turtle
yago:COVID-19  rdf:type  yago:CoronavirusDisease .   # instance of, not subclass
```

not as a `rdfs:subClassOf` that makes COVID-19 a class.

---

### Comparison with biological taxonomy

|                                   | Bio-taxonomy (Canis lupus)                  | Disease (COVID-19)                             |
| --------------------------------- | ------------------------------------------- | ---------------------------------------------- |
| Is the class role useful?         | Yes, individual wolves exist as KB entities | No, individual cases are not in YAGO           |
| Are entity-level facts important? | Yes (parentTaxon, conservation status)      | Yes (ICD code, pathogen, symptoms, start date) |
| YAGO's choice                     | instance (flatten to taxon)                 | class (P279 wins)                              |
| Information lost                  | cannot type individual wolves               | loses all entity-level facts                   |

Paradoxically, YAGO makes the opposite choice in the two cases, and loses something important in both.

For biological taxonomy, YAGO correctly prefers the instance role because the entity-level facts (parentTaxon, conservation status) are well-defined. For diseases, YAGO incorrectly prefers the class role because no instanceIndicator fires, even though the entity-level facts are equally important.

---

### The instanceIndicator asymmetry

The instanceIndicator mechanism is asymmetric:

- Biological taxa are protected by `wdt:P171` (parent taxon) — YAGO recognizes this as an instance signal
- Products are protected by `wdt:P176` / `wdt:P178` — YAGO recognizes this
- Events are protected by `wdt:P580` (start time) - but only for direct properties
- Diseases have no dedicated instanceIndicator

A disease like COVID-19 might be protected by adding `wdt:P780` (symptoms) or `wdt:P557` (ICD code) to instanceIndicators. If an entity has symptoms or an ICD code, it is a disease instance, not a class.

---

### Analysis by formalism

| Formalism | How it handles it                                                              | Pros              | Cons                                              |
| --------- | ------------------------------------------------------------------------------ | ----------------- | ------------------------------------------------- |
| OWL 2     | explicit punning — same IRI as both class and individual                       | formally correct  | requires OWL 2 DL, not supported in all reasoners |
| Wikidata  | both P31 and P279, no resolution                                               | pragmatic         | no single clear interpretation                    |
| SNOMED CT | diseases are concepts, not classes; subsumption is P279-like but concept-level | medically correct | complex model, not RDF-native                     |
| YAGO 4.5  | class (if P279 present and no instanceIndicator)                               | avoids punning    | loses all entity facts; class role is unused      |

---

### Why do we need both here?

Without COVID-19 as a class:

- Cannot type individual cases as `rdf:type yago:COVID-19`
- But: individual cases are not in YAGO, so this is a theoretical loss only

Without COVID-19 as an instance:

- Cannot attach ICD code, pathogen, symptoms, start date, treatments
- This is a real, practical loss, these are the main facts one wants about a disease

**Verdict**: following this firts very brief analysis i think COVID-19 should be an instance of `schema:MedicalEntity`, not a class. The P279 in Wikidata should be translated as a `rdf:type` fact (COVID-19 is an instance of coronavirus disease, which is a YAGO class), not as `rdfs:subClassOf` that makes COVID-19 itself a class.

---

## Questions

- [ ] check if YAGO include any individual disease instances with entity-level facts, or does every disease with P279 become a class?
- [ ] What would it take to add a disease-specific instanceIndicator (e.g., P780 symptoms, P557 ICD code)?
- [ ] try to see how does SNOMED CT's concept model compare to the YAGO class/instance choice?
- [ ] Are there diseases in YAGO that correctly end up as instances (because they lack P279)?
- [ ] Compare Wikidata vs. MeSH treatment of disease classification
