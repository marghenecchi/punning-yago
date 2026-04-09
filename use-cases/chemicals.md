# Use Case: Chemical Substances

## Example: Water (H₂O) and Aspirin

### The problem

In Wikidata, a specific chemical like water (Q283) carries simultaneously:

- `wdt:P279` (subclass of): _oxide_, _dihydrogen oxide_
- `wdt:P31` (instance of): _type of chemical entity_
- Entity-level facts: molecular formula, boiling point, CAS number, density, etc.

This is punning: water is used as a class ("every water molecule is H₂O") and as an instance (it has a specific molecular formula, a specific boiling point, a CAS registry number).

The pattern holds across the chemical domain:

| Chemical      | P279 (subclass of)           | Key entity facts                            |
| ------------- | ---------------------------- | ------------------------------------------- |
| Water (H₂O)   | chemical compound, oxide     | mol. formula H₂O, bp 100°C, CAS 7732-18-5   |
| Methane (CH₄) | alkane, organic compound     | mol. formula CH₄, bp -161°C, CAS 74-82-8    |
| Aspirin       | NSAID, salicylate, analgesic | mol. formula C₉H₈O₄, CAS 50-78-2, mol. wt.  |
| Ethanol       | alcohol, organic solvent     | mol. formula C₂H₅OH, bp 78.4°C, CAS 64-17-5 |

---

### The chemical taxonomy

The Wikidata chemical taxonomy is very deep:

```
chemical entity (Q43460564)          ← mapped to schema:BioChemEntity
  └── chemical substance (Q79529)
        └── chemical compound (Q11173)
              └── organic compound (Q11174)
                    └── carboxylic acid
                          └── salicylate
                                └── aspirin
```

Each node in this chain has `wdt:P279` (subclass of) pointing to its parent. Specific chemicals like aspirin are at the leaves of this tree and also have entity-level facts.

---

### How YAGO handles it

#### The `schema:BioChemEntity` mapping and `badClasses`

The YAGO schema maps `schema:BioChemEntity` from Wikidata via (as of 08/04/2026 i think):

```turtle
schema:BioChemEntity a sh:NodeShape ;
    rdfs:subClassOf schema:Thing ;
    sh:property [
        sh:path yago:chemicalStructure ;
        sh:datatype xsd:string ;
        ys:fromProperty wdt:P274 ;   # molecular formula, e.g. "H2O"
    ] ;
    ys:fromClass wd:Q43460564, wd:Q55568967 .
```

At the same time, `make-taxonomy.py` lists Q43460564 in `badClasses`:

```python
badClasses = {
    ...
    "wd:Q43460564",   # Chemical entity
    ...
}
```

These two facts seem contradictory, but they serve different roles:

- The `badClasses` entry prevents Q43460564 itself from being inserted as a node in the YAGO taxonomy (it would be a very broad, meta-level class).
- The `ys:fromClass` mapping tells the taxonomy builder: look at the **direct children** of Q43460564 in Wikidata's P279 graph and add them as subclasses of `schema:BioChemEntity`.

```python
# make-taxonomy.py, main loop
for yagoClass in yagoSchema.classes.values():
    for wikidataClass in yagoClass.fromClasses:
        for wikidataSubclass in wikidataTaxonomyDown.get(wikidataClass, []):
            addSubClass(yagoClass.identifier, wikidataSubclass, ...)
```

So Q79529 (chemical substance), Q11173 (chemical compound), etc. (the direct children of Q43460564) are added to the YAGO taxonomy as subclasses of `schema:BioChemEntity`. Their descendants (organic compounds, specific drugs, etc.) are added recursively.

#### Step 02 (`make-taxonomy.py`)

Specific chemicals (H₂O, aspirin) have `wdt:P279` (subclass of their parent class in the taxonomy) but none of the `instanceIndicators`:

```python
instanceIndicators = {
    "wdt:P171",  # parent taxon
    "wdt:P176",  # manufacturer
    "wdt:P178",  # developer
    "wdt:P580"   # start time
}
```

No instanceIndicator fires. The WikidataVisitor sees `wdt:P279` → adds H₂O and aspirin to `wikidataTaxonomyDown`. The taxonomy builder recurses into the chemical hierarchy and eventually adds both as YAGO classes.

Result: H₂O and aspirin end up in `yagoTaxonomyUp` as classes (subclasses of schema:BioChemEntity via the chemical taxonomy chain).

#### Step 03 (`make-facts.py`)

Since H₂O is in `yagoTaxonomyUp`, `make-facts.py` immediately assigns it `rdf:type rdfs:Class` and returns:

```python
if mainEntity in yagoTaxonomyUp:
    entityFacts.add((mainEntity, Prefixes.rdfType, Prefixes.rdfsClass))
    return declaredWikidataTypes   # returns immediately
```

Then `handleDomain` runs with `fullTransitiveClasses = {"rdfs:Class"}`. The domain of all chemical properties (`yago:chemicalStructure`, `yago:contains`, `yago:interacts`) is `schema:BioChemEntity`, not `rdfs:Class`. Domain check fails. All entity-level facts are dropped.

What YAGO keeps for H₂O:

```turtle
yago:Water  rdf:type         rdfs:Class .
yago:Water  rdfs:subClassOf  yago:Oxide .        # via taxonomy
yago:Water  rdfs:label       "water"@en .
```

What is lost:

```turtle
yago:Water  schema:molecularFormula  "H2O" .
yago:Water  yago:boilingPoint        "100"^^yago:Celsius .
yago:Water  yago:meltingPoint        "0"^^yago:Celsius .
yago:Water  yago:density             "1.0"^^yago:GramsPerCubicCentimetre .
yago:Water  yago:casNumber           "7732-18-5" .
yago:Water  yago:chemicalStructure   <...> .
```

Same for aspirin: it becomes a class, all pharmaceutical facts (molecular weight, CAS number, ATC code, mechanism of action, drug interactions) are dropped.

---

### This is the disease problem, applied to chemistry

The mechanism is identical to the disease case (COVID-19):

|                               | Disease (COVID-19)                    | Chemical (H₂O / aspirin)               |
| ----------------------------- | ------------------------------------- | -------------------------------------- |
| Has `wdt:P279`?               | Yes                                   | Yes                                    |
| instanceIndicator fires?      | No (P580 only on qualified statement) | No (no manufacturer, no start time)    |
| YAGO step 02 result           | class in taxonomy                     | class in taxonomy                      |
| Entity-level facts in step 03 | all dropped by domain check           | all dropped by domain check            |
| Is the class role useful?     | No (individual cases not in YAGO)     | No (individual molecules not in YAGO)  |
| Is the instance role useful?  | Yes (ICD code, pathogen, symptoms)    | Yes (mol. formula, CAS, boiling point) |

In both cases, the entity ends up as a class, and the class role is useless, nobody types individual COVID-19 cases or individual water molecules in YAGO.

The difference is that chemicals have a much deeper and more systematic taxonomy, so the problem affects a larger fraction of the KB. Almost every specific chemical in Wikidata has P279.

---

### The instanceIndicator gap

For the disease case, a possible fix was to add `wdt:P780` (symptoms) or `wdt:P557` (ICD code) as instanceIndicators. The same logic applies here: certain Wikidata properties reliably indicate that an entity is a specific chemical substance, not an abstract class:

- `wdt:P231` (CAS registry number) — if an entity has a CAS number, it is a specific chemical substance
- `wdt:P274` (chemical formula) — if an entity has a molecular formula, it is a specific compound
- `wdt:P2067` (molecular mass) — same reasoning

If any of these were added to `instanceIndicators`, specific chemicals like H₂O and aspirin would be excluded from the taxonomy in step 02. They would then need a valid type via P31 — which for chemicals points to classes like "chemical compound" (Q11173) that ARE in the YAGO taxonomy (as subclasses of BioChemEntity). So the typing in step 03 would succeed, and the entity facts would be preserved.

---

### What would be gained

With H₂O and aspirin as instances of `schema:BioChemEntity`, the currently defined property would be preserved:

```turtle
yago:Water    rdf:type                  schema:BioChemEntity .
yago:Water    yago:chemicalStructure    "H2O" .       # via wdt:P274

yago:Aspirin  rdf:type                  schema:BioChemEntity .
yago:Aspirin  yago:chemicalStructure    "C9H8O4" .
```

The property set is currently minimal (`yago:chemicalStructure` from P274 is the only active property on `schema:BioChemEntity`, after `yago:interacts` and `yago:contains` were removed as "Too few facts"). Other chemical properties (boiling point, CAS number, molecular mass) could be added to the schema to make the class more useful.

---

### Comparison with products

|                        | Product (iPhone 13)                  | Chemical (H₂O)                      |
| ---------------------- | ------------------------------------ | ----------------------------------- |
| Has instanceIndicator? | Yes (P176 manufacturer)              | No                                  |
| Step 02 result         | excluded from taxonomy (instance)    | in taxonomy (class)                 |
| Step 03 result         | disappears (P31 fails: second-order) | entity facts dropped (domain check) |
| Intended YAGO class    | `schema:Product`                     | `schema:BioChemEntity`              |
| Actual YAGO presence   | invisible (meta file only)           | exists as class, no facts           |

Products disappear entirely because two mechanisms fail in sequence. Chemicals survive in YAGO but only as empty classes, because no instanceIndicator protects them from the taxonomy.

---

### Analysis by formalism

| Formalism   | How it handles it                                                                 | Pros                 | Cons                                         |
| ----------- | --------------------------------------------------------------------------------- | -------------------- | -------------------------------------------- |
| OWL 2       | explicit punning — H₂O as class (of molecules) and individual (with formula)      | formally correct     | complex; molecules not represented anyway    |
| Wikidata    | P31 + P279 co-exist; entity facts on the item                                     | pragmatic, data-rich | no single interpretation                     |
| ChEBI       | chemicals are ontology classes; entity facts are class annotations                | chemically rigorous  | not RDF-instance model; complex for SPARQL   |
| PubChem CID | each compound is an individual with a CID; hierarchy via classification           | instance-centric     | no standard RDF taxonomy                     |
| YAGO 4.5    | chemical taxonomy preserved; specific chemicals become classes; entity facts lost | taxonomy correct     | all instance-level chemistry data is dropped |

---

### Why do we need class here?

Without H₂O as a class:

- Cannot type individual molecules as `rdf:type yago:Water`
- But individual molecules are never represented in YAGO

Without H₂O as an instance:

- Cannot attach molecular formula, boiling point, density, CAS number
- These are the primary facts one wants about a chemical substance

**Verdict**: H₂O should be an instance of `schema:BioChemEntity` (or a class like `yago:ChemicalCompound`), not a YAGO class. The P279 in Wikidata ("every water molecule is a chemical compound") should inform the type assignment (H₂O is a kind of chemical compound), not make H₂O a class in the YAGO taxonomy. The fix is to add chemical-specific instanceIndicators such as `wdt:P231` (CAS number) or `wdt:P274` (chemical formula).

---

## Questions

- [ ] After adding a chemical instanceIndicator, would P31-based typing succeed? (e.g., H₂O has P31 = "chemical substance" Q79529, which is in yagoTaxonomyUp as a subclass of BioChemEntity)
- [ ] How does ChEBI's class-annotation model compare to the YAGO approach for encoding chemical properties?
- [ ] Are there chemicals in Wikidata that currently end up as `schema:BioChemEntity` instances (because they have P31 directly pointing to Q43460564 or Q55568967)?
