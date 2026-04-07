# Formalisms, how they differently handle punning

## Formalisms to analyze

| Formalism                     | File                       | Status      |
| ----------------------------- | -------------------------- | ----------- |
| OWL 2                         | [owl.md](owl.md)           | todo        |
| RDF / RDFS                    | [rdf.md](rdf.md)           | todo        |
| Wikidata                      | [wikidata.md](wikidata.md) | todo        |
| Description Logic             | [dl.md](dl.md)             | todo        |
| SKOS                          | [skos.md](skos.md)         | todo        |
| YAGO 4.5 (Schema.org + SHACL) | [yago.md](yago.md)         | in progress |

---

## YAGO 4.5 (summary of how it works)

YAGO does not use plain OWL. Its formalism is a combination of:

- **Schema.org** for the class taxonomy (top-level vocabulary)
- **SHACL NodeShapes** for property constraints and validation
- **RDFS** for `rdfs:subClassOf` and `rdfs:Class`
- **OWL** only for `owl:disjointWith` and `owl:sameAs`

### Class definition in YAGO (from yago-schema.ttl)

```turtle
schema:Person a sh:NodeShape, rdfs:Class ;
  rdfs:subClassOf schema:Thing ;
  owl:disjointWith schema:Event, schema:Organization, schema:Place,
                   schema:Product, schema:Taxon, schema:CreativeWork ;
  ys:fromClass wd:Q5, wd:Q215627 ;
  sh:property [
    sh:path schema:birthDate ;
    sh:datatype xsd:date ;
    sh:maxCount 1 ;
    ys:fromProperty wdt:P569 ;
  ] .
```

### Instance definition in YAGO (from stage 05 output)

```turtle
yago:Elvis rdf:type yago:Singer, schema:Person, schema:Thing ;
  owl:sameAs wd:Q_Elvis ;
  schema:birthDate "1935"^^xsd:gYear ;
  schema:mainEntityOfPage <https://en.wikipedia.org/wiki/Elvis> .
```

### Punning in YAGO

```turtle
# Singer is a CLASS (used as type target):
yago:Elvis rdf:type yago:Singer .

# Singer is also an INSTANCE (of rdfs:Class):
yago:Singer rdf:type rdfs:Class .
yago:Singer owl:sameAs wd:Q_singer .
```

YAGO allows this meta-level punning (every class is an instance of rdfs:Class)
but filters out object-level punning (entities that are simultaneously instances of disjoint classes).

---

## Key insight: YAGO's formalism is a hybrid

YAGO 4.5 is not based on any single standard formalism.
It is an **engineered hybrid** that:

1. Uses Schema.org classes as a controlled vocabulary
2. Uses SHACL for property validation (not reasoning)
3. Uses RDFS for the class hierarchy
4. Uses OWL disjointness to catch cross-domain punning
5. Filters out entities that cannot fit the hierarchy rather than representing them

This means the question "how does YAGO handle punning" is currently: it doesn't, it remove it.
The internship goal is to find a better answer :)
