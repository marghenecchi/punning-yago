# Use Case: Academic Disciplines

## Example: Computer Science > Artificial Intelligence > Machine Learning

### The problem

Academic disciplines form hierarchies where each field is both an instance (of a broader field or academic category) and a class (of subfields, courses, publications):

```
Academic field
  └── Computer Science    ← instance of "academic field" AND class of CS subfields
        └── Artificial Intelligence    ← instance of CS AND class of AI subfields
              └── Machine Learning    ← instance of AI AND class of ML papers/courses
                    └── [specific paper or course]    ← instance of Machine Learning
```

Statements on "Machine Learning":

| Statement                                    | Type              | Subject is...            |
| -------------------------------------------- | ----------------- | ------------------------ |
| `ML subFieldOf AI`                           | taxonomic fact    | field-as-entity          |
| `ML usesStatisticalMethods true`             | generic fact      | field-as-kind            |
| `Paper123 rdf:type MachineLearning`          | instance typing   | ML as a class            |
| `ML namedBy ArthurSamuel`                    | entity fact       | field-as-entity          |
| `ML emergencePeriod 1950s`                   | entity fact       | field-as-entity          |

### What makes this structurally different from biological taxonomy

- **Disciplines are defined by communities of practice**, not by formal criteria — boundaries shift and are contested
- **Interdisciplinary overlap is the norm**: a paper can be classified under ML, Statistics, and Neuroscience simultaneously — multi-class membership is expected
- **The taxonomy is not hierarchical in practice**: CS and Mathematics overlap; Computational Biology is neither purely CS nor purely Biology
- **Role-dependent classification**: the same entity "Machine Learning" is a class for papers but an instance for a curriculum and an entity for a funding body

### Special cases

- Disciplines that merged or split over time (Cybernetics → AI + Control Theory)
- Applied vs. theoretical variants (Pure Mathematics vs. Applied Mathematics)
- Journals that define field boundaries: is a paper in "Nature Machine Intelligence" automatically an instance of ML?

---

## How YAGO handles it

TODO

---

## Analysis by formalism

TODO

---

## Why do we need class here?

Without "Machine Learning" as a class:
- Cannot type papers, courses, or researchers as instances of the field
- Cannot query "all papers in Machine Learning" via class membership

Without "Machine Learning" as an instance:
- Cannot attach history, key figures, major venues to the field entity

---

## Questions

- [ ] Does YAGO represent academic disciplines and how does it type them?
- [ ] How does Wikidata distinguish P31 (instance of academic discipline) from P279 (subclass of broader field)?
- [ ] How to handle interdisciplinary works — is this a problem for the class model?
- [ ] Is the field/subfield relationship better modeled as `rdfs:subClassOf` or `schema:isPartOf`?
