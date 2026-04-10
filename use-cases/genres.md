# Use Case: Cultural Genres

## Example: Rock > Classic rock > British Invasion

### The problem

Genre hierarchies in music, film, and literature create structures where each genre is both an instance (of a broader genre or cultural category) and a class (of works or more specific genres):

```
Musical genre
  └── Rock music    ← instance of "musical genre" AND class of rock works/subgenres
        └── Classic rock    ← instance of Rock AND class of classic rock works
              └── British Invasion    ← instance of Classic rock AND class of works
                    └── [specific album]    ← instance of British Invasion
```

Statements on "Rock music":

| Statement                      | Type            | Subject is...   |
| ------------------------------ | --------------- | --------------- |
| `Rock originYear 1950s`        | entity fact     | genre-as-entity |
| `Rock usesElectricGuitar true` | generic fact    | genre-as-kind   |
| `HelpAlbum rdf:type Rock`      | instance typing | Rock as a class |
| `Rock subgenreOf PopMusic`     | taxonomic fact  | genre-as-entity |
| `Rock influencedBy Blues`      | entity fact     | genre-as-entity |

### What makes this structurally different from biological taxonomy

- **Genres are not discrete**: works can belong to multiple genres simultaneously (multi-class membership), unlike biological species which typically have one parent taxon
- **Genre boundaries are contested and shift over time**: "progressive rock" vs. "art rock" — the class extension is fuzzy and socially constructed
- **Generic facts are weaker**: "rock uses electric guitar" admits many more exceptions than "wolves are carnivores"; genre properties are more like tendencies or family resemblances
- **The taxonomy is not authoritative**: there is no official genre registry; different sources give different hierarchies

### Special cases

- Works that define or create a genre retroactively
- Genres that merge (R&B + Rock → Rock and Roll)
- Artists whose genre is contested or evolves over a career
- Film vs. music genres: structurally similar but different community practices

---

## How YAGO handles it

YAGO resolves the genre punning by forcing a binary choice at ingestion time:

**Genres that have P279 (subclass of) links in Wikidata are treated as classes.** They are incorporated into the YAGO taxonomy by `02-make-taxonomy.py`, which traverses the Wikidata P279 hierarchy and builds `rdfs:subClassOf` chains. "Rock music" → "Classic rock" → "British Invasion" becomes a class hierarchy.

**Works that have P136 (genre) are assigned `rdf:type` pointing to the genre class.** In `03-make-facts.py`, P136 is listed as a `TYPE_PREDICATE` alongside P31 (instance of) and P106 (occupation). When a work has `P136 → Rock music`, and Rock music is a YAGO taxonomy class, YAGO emits `work rdf:type <Rock music>`.

```python
# 03-make-facts.py, line 112
TYPE_PREDICATES = [
    Prefixes.wikidataType,       # P31 - instance of
    Prefixes.wikidataOccupation, # P106 - occupation
    Prefixes.wikidataGenre,      # P136 - genre  ← genre used as type generator
    Prefixes.wikidataPosition    # P39 - position held
]
```

**The instance role of genres is dropped.** In Wikidata, "Rock music" has `P31 → musical genre` (it is an instance of the category "musical genre"). But `03-make-facts.py` checks: if the entity is already in the taxonomy (i.e., it is a class), it adds `rdf:type rdfs:Class` and returns immediately without processing any P31 assertions:

```python
if mainEntity in yagoTaxonomyUp:
    entityFacts.add((mainEntity, Prefixes.rdfType, Prefixes.rdfsClass))
    return declaredWikidataTypes   # ← P31 facts about Rock music are never processed
```

So "Rock music" in YAGO is a class but is NOT an instance of "musical genre". Its entity-level facts (origin period, geographic origin, cultural influences) are still stored as triples on the same IRI, lwhich is also used as a class, but without any explicit disambiguation: this is silent RDF-level punning.

**Multi-genre membership** is handled naturally: a work with P136 pointing to several genres (e.g., both Rock and Folk) receives multiple `rdf:type` assertions, which is valid RDF. No special treatment is needed.

In practice, P136 does not produce any output in the current YAGO schema. The mechanism above works only if the genre class is in `yagoTaxonomyUp`. For that to happen, musical genres (Q188451 in Wikidata) or one of their ancestors must be mapped via `ys:fromClass` to a YAGO class — and no such mapping exists in the current schema. As a result:

- "Rock music" and all other musical genres are not added to `yagoTaxonomyUp` in step 02
- The P136-based type check in step 03 fails for every album: `if obj in yagoTaxonomyUp` → False → no `rdf:type` is added, and the P136 triple is removed
- Genre information for musical works disappears entirely from YAGO

The code infrastructure for P136 typing is in place (`TYPE_PREDICATES`), but it is effectively dead because no genre class is anchored in the YAGO schema. Adding a `yago:MusicGenre` class with `ys:fromClass wd:Q188451` would activate it.

---

## Analysis by formalism

### RDF / RDFS

RDF has no barrier against the same IRI being both a class and an individual, so the genre hierarchy is technically expressible:

```turtle
ex:RockMusic  rdfs:subClassOf  ex:MusicalGenre .          # Rock as a class
ex:RockMusic  rdf:type         ex:MusicalGenre .           # Rock as an instance — valid in RDF
ex:RockMusic  ex:originPeriod  "1950s" .                   # entity fact — coexists silently
ex:HelpAlbum  rdf:type         ex:RockMusic .              # album typed as Rock
```

All four triples are valid. But RDFS creates an inference risk: if `ex:originPeriod rdfs:domain ex:CulturalEntity`, then the triple `RockMusic ex:originPeriod "1950s"` entails `RockMusic rdf:type ex:CulturalEntity`. This fires on RockMusic-as-class (intended) but may also propagate to albums through the `rdfs:subClassOf` chain in unexpected ways if the domain/range vocabulary is not carefully designed.

The multi-genre property `ex:influencedBy` creates a further problem: `RockMusic ex:influencedBy Blues` looks like an individual fact, but if it has `rdfs:domain ex:CulturalEntity`, RDFS will infer `Blues rdf:type ex:CulturalEntity` too, which may or may not be intended.

Generic facts (typical instrumentation, tempo range) cannot be expressed distinctly from entity facts: both are triples on the same IRI, and RDFS has no mechanism to mark one as "about the genre as a kind" rather than "about the genre as an individual".

### OWL 2

OWL 2 DL explicitly supports genre punning via its two-domain semantics:

```turtle
ex:RockMusic  rdf:type          owl:Class .
ex:RockMusic  rdfs:subClassOf   ex:MusicalGenre .        # class role: TBox
ex:RockMusic  rdf:type          ex:CulturalMovement .    # individual role: ABox
ex:RockMusic  ex:originPeriod   "1950s" .                # individual fact
```

Under OWL 2 DL, the class interpretation and the individual interpretation (the entity Rock music with its origin date) are in separate semantic domains. Domain/range inferences on individual-role triples do not affect the class extension.

However:

- **Generic facts remain inexpressible.** "Rock music typically uses electric guitar" is neither an assertion about the individual Rock music entity (`ex:RockMusic ex:uses ex:ElectricGuitar` as an ABox fact) nor a universal class restriction (`rdfs:subClassOf (ex:uses only ex:ElectricGuitar)` is too strong and incorrect). OWL 2 has no construct for tendential or default properties.
- **Multi-genre membership** is unproblematic: OWL 2 allows multiple `rdf:type` assertions.
- **Fuzzy boundaries**: "genre" in OWL is a crisp set. The contested, socially constructed nature of genre boundaries (is this album progressive rock or art rock?) cannot be represented, a work is either an instance or not.
- **No connection between the two roles**: the OWL two-domain semantics means there is no formal link between the class "Rock music" (its extension of works) and the individual "Rock music" (its historical origin). Properties of the class (size, typical members) cannot be referenced from the individual.

### Summary

| Aspect                      | RDF/RDFS                              | OWL 2 DL                                            | YAGO                                       |
| --------------------------- | ------------------------------------- | --------------------------------------------------- | ------------------------------------------ |
| Genre as class + instance   | Allowed, implicit                     | Allowed, two-domain                                 | Class only (instance role dropped)         |
| Entity facts on genre       | Stored silently alongside class facts | Stored on individual, separated semantically        | Stored on class IRI, no disambiguation     |
| Generic facts (tendencies)  | Not distinguishable from entity facts | Not expressible (universal restrictions too strong) | Not representable                          |
| Multi-genre membership      | Multiple `rdf:type`, fine             | Multiple `rdf:type`, fine                           | Multiple `rdf:type`, handled naturally     |
| Fuzzy genre boundaries      | Not representable                     | Not representable                                   | Not representable                          |
| Domain/range inference risk | Yes, fires on class-role triples      | Contained to individual role                        | Not applicable (YAGO avoids OWL reasoning) |

---

## Why do we need class here?

Without "Rock music" as a class:

- Cannot type works as instances of the genre
- Cannot query "all rock albums" via class membership
- Cannot inherit generic properties (tempo range, typical instrumentation) to works

Without "Rock music" as an instance:

- Cannot attach origin date, geographic origin, cultural influences

---

## Questions

- [ ] How does Wikidata represent genre membership (P136 instance-side vs. P279 for genre hierarchy)?
- [ ] Does YAGO include genre entities and how does it type them?
- [ ] How to handle multi-genre membership — is this a problem for the class model?
- [ ] Are genre generic facts (tempo, instrumentation) representable as class-level restrictions in OWL?
