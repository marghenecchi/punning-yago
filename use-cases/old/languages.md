# Use Case: Languages

## Example: Italian, Romance languages

### The problem

In Wikidata, specific languages have both:

- `wdt:P279` (subclass of): _Romance language_, _Indo-European language_, _natural language_
- `wdt:P31` (instance of): _language_, _living language_, _modern language_

Languages also form a deep classification hierarchy:

```
Natural language
  └── Indo-European language
        └── Italic language
              └── Romance language
                    └── Italian    ← class of dialects/varieties OR instance of Romance?
                          └── Tuscan
                          └── Sicilian
                          └── Venetian
```

Each node in this hierarchy carries both P279 (toward the parent) and P31 (toward "language"). Classic punning at every level.

---

### How YAGO handles it

#### Step 02 (`make-taxonomy.py`)

Languages have no `instanceIndicators` (no P171, P176, P178, P580). So any language entity with `wdt:P279` becomes a YAGO class. The entire language taxonomy (families, branches, individual languages, dialects) ends up in `yagoTaxonomyUp`.

`schema:Language` has `ys:fromClass wd:Q34770` (language). All Wikidata entities with P279 pointing up to Q34770 become subclasses of `schema:Language`.

#### Step 03 (`make-facts.py`)

Languages in `yagoTaxonomyUp` get `rdf:type rdfs:Class` and lose their entity-level facts via the domain check, same mechanism as diseases.

**But**: `schema:Language` has no properties defined in the YAGO schema:

```turtle
schema:Language a sh:NodeShape ;
    rdfs:subClassOf schema:Intangible ;
    ys:fromClass wd:Q34770, wd:Q17376908 .
    # no sh:property blocks
```

So there is no domain to fail against. Languages as instances would already have no YAGO-defined properties. The Wikidata facts about languages (ISO code, number of speakers, writing system, P1412 speakers...) are simply not mapped in the YAGO schema.

The real problem for languages is not that entity facts are lost, it is what happens when languages are used as objects of other properties.

Languages appear as range values of:

| Property                | Domain                | Wikidata source |
| ----------------------- | --------------------- | --------------- |
| `schema:inLanguage`     | `schema:CreativeWork` | P364, P407      |
| `schema:knowsLanguage`  | `schema:Person`       | P1412           |
| `yago:nativeLanguage`   | `schema:Person`       | P103            |
| `yago:officialLanguage` | `schema:Country`      | P37             |

In step 03, these facts survive the range check because `cleanObject` accepts any entity as a valid object when the range type is a class (not a datatype). A fact like:

```
yago:Divina_Commedia  schema:inLanguage  yago:Italian  . # IF schema:Language
```

passes step 03 and reaches step 04.

#### Step 04 (`make-typecheck.py`), the key breakage

Step 04 enforces the range type check using `instanceOf`:

```python
if classes is None or any(instanceOf(obj, c) for c in classes):
    out.write(subject, predicate, obj, ...)          # object is an instance → keep
elif any(isSubclassOf(obj, c) for c in classes):
    newObject = createGenericInstance(obj, out)
    out.write(subject, predicate, newObject, ...)    # object is a subclass → replace with blank node
else:
    logFile.writeMetaFact(...)                       # object is neither → drop
```

For `yago:Divina_Commedia schema:inLanguage yago:Italian . # IF schema:Language`:

- `instanceOf(yago:Italian, schema:Language)` → checks `yagoInstances[yago:Italian]` = `{"rdfs:Class"}` → `isSubclassOf("rdfs:Class", "schema:Language")` = False → **fails**
- `isSubclassOf(yago:Italian, schema:Language)` → checks `yagoTaxonomyUp`: Italian is a subclass of schema:Language → **True**

The `elif` branch fires. A generic blank node is created:

```turtle
_:Italian_generic_instance  rdf:type  yago:Italian .
```

And the original fact becomes:

```turtle
yago:Divina_Commedia  schema:inLanguage  _:Italian_generic_instance .
```

The direct link to `yago:Italian` is replaced by an anonymous blank node. The connection to the language entity is broken.

---

### What is lost

Unlike diseases, the primary loss for languages is not entity-level facts (which were never in the YAGO schema), it is the reference integrity of language links.

| What you want to query                    | What YAGO gives you                                               |
| ----------------------------------------- | ----------------------------------------------------------------- |
| "Which books are written in Italian?"     | Results point to `_:Italian_generic_instance`, not `yago:Italian` |
| "What language does Dante speak?"         | `schema:knowsLanguage _:Italian_generic_instance`                 |
| "What is the official language of Italy?" | `yago:officialLanguage _:Italian_generic_instance`                |

You can still traverse `_:English_generic_instance rdf:type yago:English` to reach the language class, but:

- The direct link is gone
- Every blank node is a different anonymous entity, you cannot join queries across them
- `yago:English` as a class entity has no queryable facts

---

### Comparison with diseases

|                                    | Diseases (COVID-19)                                 | Languages (English)                                      |
| ---------------------------------- | --------------------------------------------------- | -------------------------------------------------------- |
| Entity-level facts in YAGO schema? | Yes (`yago:symptom`, `yago:treatment`, ICD code...) | No (ISO code, speakers, writing system not mapped)       |
| Primary loss                       | Entity facts dropped by domain check (step 03)      | Language references replaced by blank nodes (step 04)    |
| Used as range value?               | Rarely                                              | Yes — central use case                                   |
| Generic instance created?          | Possibly, but rarely encountered                    | Always, for every `inLanguage`, `officialLanguage`, etc. |

---

### Analysis by formalism

| Formalism | How it handles it                                       | Pros                 | Cons                                        |
| --------- | ------------------------------------------------------- | -------------------- | ------------------------------------------- |
| RDF/RDFS  | language IRI appears as class (in P279 hierarchy) and as object of `inLanguage`, `officialLanguage`; no barrier to this in RDF | permissive | without punning semantics, any system processing the graph must choose: is `yago:Italian` a class or a stable entity to link to? RDFS offers no mechanism to signal intent; domain/range inference on properties like `schema:inLanguage` (range `schema:Language`) would type Italian as a language instance, but Italian is already flagged as a class — the two inferences conflict |
| OWL 2     | two-domain punning: Italian as class (of dialects/varieties, if useful) and individual (referenceable entity in `inLanguage`, `officialLanguage` triples); the individual role is exactly what YAGO's step 04 tries to patch with blank nodes | formally solves the reference problem | requires OWL 2 DL; the class role (Italian as a class of dialects) is weaker than in animals or chemicals — the extension is fuzzy |
| Wikidata  | P31 and P279 coexist on the same item                   | pragmatic            | no single clear interpretation              |
| Glottolog | pure hierarchy, no instance facts                       | linguistically clean | not a KR system                             |
| YAGO 4.5  | class (P279 wins, no instanceIndicator)                 | taxonomy preserved   | language references replaced by blank nodes |

Note: languages are the only use case where the punning problem manifests primarily as a **reference integrity failure** rather than a data loss. The step 04 blank node workaround (`_:Italian_generic_instance rdf:type yago:Italian`) is YAGO's ad hoc substitute for OWL 2's individual role: it creates a stable referent for the language as an object of properties, but breaks join queries because blank nodes lack a stable IRI identity.

---

### Why do we need both?

As a class (in the taxonomy):

- `English rdfs:subClassOf WestGermanicLanguage rdfs:subClassOf GermanicLanguage ...`
- Dialects and varieties are subclasses: `AmericanEnglish rdfs:subClassOf English`
- Legitimate and important for linguistic classification

As an instance (as a referenceable entity):

- Can be the direct object of `schema:inLanguage`, `yago:officialLanguage`, `schema:knowsLanguage`
- Can be joined across facts: "what books are written in the official language of France?"
- Without a stable entity identity, cross-fact queries over languages break

The punning problem is that the taxonomy role (class) and the reference role (instance, as a stable entity to point to) cannot coexist in YAGO's binary model. The generic instance mechanism in step 04 is a symptom of this: YAGO detects that a class is being used where an instance was expected, and creates a throwaway blank node as a workaround.

---

## Questions

- [ ] Does the generic instance get reused (one blank node per language class) or recreated for every fact?
- [ ] How does the generic instance mechanism interact with queries, can SPARQL join over blank nodes?
- [ ] Are dialects and language varieties (Sicilian, Venetian, Old Italian) handled differently from language entities?
- [ ] Should `schema:Language` have properties defined (ISO code, writing system, number of speakers)? Would that change anything?
