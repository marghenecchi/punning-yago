# Use Cases — Punning Analysis

For each use case I plan to analyze:

- How punning manifests (is the entity both a class and an instance?)
- How different formalisms handle it (OWL, RDF, Wikidata, SKOS...)
- Open problems and trade-offs

---

## Use Cases

| File                                               | Domain               | Key example            | Status  | Structure                        |
| -------------------------------------------------- | -------------------- | ---------------------- | ------- | -------------------------------- |
| [products.md](products.md)                         | Commercial products  | todo                   | todo    | class/instance hierarchy         |
| [diseases.md](diseases.md)                         | Diseases             | draft                  | COVID19 | class/instance hierarchy         |
| [animals.md](animals.md)                           | Biological taxonomy  | Canis lupus            | draft   | deep taxonomy, generic sentences |
| [languages.md](languages.md)                       | Languages            | todo                   | todo    | class/instance hierarchy         |
| [chemicals.md](chemicals.md)                       | Chemical substances  | H₂O, methane           | todo    | deep taxonomy (like bio)         |
| [admin-divisions.md](admin-divisions.md)           | Administrative units | France > Île-de-France | todo    | geographic hierarchy             |
| [genres.md](genres.md)                             | Cultural genres      | Rock > Classic rock    | todo    | deep taxonomy + generic facts    |
| [event-series.md](event-series.md)                 | Recurring events     | Olympics, Nobel Prize  | todo    | temporal recurrence              |
| [software-versions.md](software-versions.md)       | Software & versions  | Python > Python 3.11   | todo    | versioning hierarchy             |
| [academic-disciplines.md](academic-disciplines.md) | Academic disciplines | Computer Science       | todo    | field/subfield hierarchy         |

---

## Important question: Why do we need class?

Each use case must also answer: would a flat approach (instances only + properties, no explicit classes) be sufficient? What information would be lost?
