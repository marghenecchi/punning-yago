# Use Case: Administrative Divisions

## Example: France > Île-de-France > Paris

### The problem

Administrative hierarchies nest geographic units where each unit is both a class (its subdivisions are instances of it) and an instance (of the level above):

```
Sovereign state
  └── France    ← instance of "sovereign state" AND class of its regions
        └── Île-de-France    ← instance of France AND class of its departments
              └── Paris (department)    ← instance of Île-de-France
                    └── Paris (commune)    ← instance or part?
```

Statements on "France":

| Statement                              | Type              | Subject is...          |
| -------------------------------------- | ----------------- | ---------------------- |
| `France capital Paris`                 | entity fact       | France-as-entity       |
| `France population 68M`                | entity fact       | France-as-entity       |
| `IleDeF rdf:type France`               | instance typing   | France as a class      |
| `France memberOf EU`                   | entity fact       | France-as-entity       |
| `France hasOfficialLanguage French`    | generic fact      | France-as-kind(?)      |

### What makes this structurally different from biological taxonomy

- **Administrative divisions are defined by law**, not by natural kinds — the class extension changes when borders change
- **Multiple overlapping hierarchies**: France can be divided by regions, departments, or NUTS codes, giving different class structures for the same entity
- **Non-disjoint levels**: a "commune" can be both a city and a department (Paris)
- **Historical changes**: Alsace-Moselle was German from 1871 to 1918. Was it an instance of France during that period? Class membership is time-indexed.

### Special cases

- Cities that are also regions or departments (Paris, Brussels)
- Disputed territories (Kosovo: instance of which class? Under whose classification?)
- Historical states that no longer exist (USSR, Yugoslavia)
- Federal vs. unitary states: US states have a different relationship to the federal level than French departments

---

## How YAGO handles it

TODO

---

## Analysis by formalism

TODO

---

## Why do we need class here?

Without France as a class:
- Cannot type regions as instances of France
- Cannot query "all administrative subdivisions of France" via class membership
- Cannot express that regions inherit certain legal facts from France

Without France as an instance:
- Cannot attach population, capital, membership in international organizations

---

## Questions

- [ ] How does Wikidata handle P31/P279 for administrative units?
- [ ] Does YAGO use `schema:containedInPlace` (part-of) instead of `rdfs:subClassOf` — and does this resolve or sidestep the punning?
- [ ] How are time-indexed class memberships handled (territories that changed country)?
- [ ] Compare with GeoNames taxonomy of administrative divisions
