# Use Case: Recurring Events

## Examples: Olympics, Nobel Prize

### The problem

A recurring event series is simultaneously:
- An **instance** of some category ("multi-sport international event series", "scientific award")
- A **class** of which each edition is an instance

```
Event series
  └── Olympics    ← instance of "multi-sport series" AND class of editions
        └── Paris 2024 Olympics    ← instance of Olympics
              └── [specific competition]    ← instance of a specific competition
```

Statements on "Olympics":

| Statement                                   | Type             | Subject is...              |
| ------------------------------------------- | ---------------- | -------------------------- |
| `Olympics foundedYear 1896`                 | entity fact      | series-as-entity           |
| `Olympics heldEvery 4 years`                | structural fact  | series-as-entity           |
| `Paris2024 rdf:type Olympics`               | instance typing  | Olympics as a class        |
| `Paris2024 location Paris`                  | edition fact     | specific edition           |
| `Olympics associatedWith IOC`               | entity fact      | series-as-entity           |

### What makes this structurally different from biological taxonomy

- **Temporal dimension**: editions are ordered in time; membership in the class is indexed by time
- **Planned recurrence**: the class has a generative rule (every 4 years), not just a post-hoc extension
- **Properties split across levels**: some properties belong to the series (founder, periodicity), others to the edition (location, year, host country), others to individual competitions within an edition
- **Cancellation**: some editions were cancelled (1940, 1944) — are they instances? non-instances? This creates boundary problems for the class extension.

### Variant: awards (Nobel Prize)

"Nobel Prize in Physics" is an instance of "Nobel Prize" (which is itself an instance of "award"), and a class of which "Nobel Prize in Physics 2023" is an instance. Two levels of punning stacked.

```
Award
  └── Nobel Prize    ← instance of Award AND class of Prize categories
        └── Nobel Prize in Physics    ← instance of Nobel Prize AND class of annual awards
              └── Nobel Prize in Physics 2023    ← instance of Nobel Prize in Physics
```

### Special cases

- Events that changed name or structure (e.g. "European Championship" vs. "Euro")
- Events that were discontinued and restarted
- Paralympic Games: subclass of Olympics or separate class?

---

## How YAGO handles it

TODO

---

## Analysis by formalism

TODO

---

## Why do we need class here?

Without "Olympics" as a class:
- Cannot type editions (`Paris2024 rdf:type Olympics`)
- Cannot query "all editions of the Olympics" via class membership
- Cannot inherit shared properties from series to editions

Without "Olympics" as an instance:
- Cannot attach founding date, governing body, periodicity to the series entity

---

## Questions

- [ ] How does Wikidata distinguish P31 (instance of) and P279 (subclass of) for event series?
- [ ] Does YAGO represent event series and editions as separate entities?
- [ ] How to handle cancelled editions in the class extension?
- [ ] Is the Nobel Prize hierarchy in Wikidata two-level punning?
