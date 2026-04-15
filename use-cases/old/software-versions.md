# Use Case: Software and Versions

## Example: Python > Python 3 > Python 3.11

### The problem

Software systems have version hierarchies where each level is both an instance (of the parent version or software category) and a class (of more specific versions or installations):

```
Programming language
  └── Python    ← instance of "programming language" AND class of Python versions
        └── Python 3    ← instance of Python AND class of Python 3.x versions
              └── Python 3.11    ← instance of Python 3 AND class of Python 3.11 installations
                    └── [specific installation on machine M]    ← concrete instance
```

Statements on "Python":

| Statement                                   | Type              | Subject is...              |
| ------------------------------------------- | ----------------- | -------------------------- |
| `Python creator GuidoVanRossum`             | entity fact       | language-as-entity         |
| `Python firstRelease 1991`                  | entity fact       | language-as-entity         |
| `Python3_11 rdf:type Python`                | instance typing   | Python as a class          |
| `Python isDynamicallyTyped true`            | generic fact      | language-as-kind           |
| `Python3_11 releaseDate 2022-10-24`         | version fact      | specific version           |

### What makes this structurally different from biological taxonomy

- **Versions are created artifacts**, not natural kinds — the class extension is controlled by a manufacturer/community
- **Backward compatibility**: Python 3.11 inherits properties from Python 3 and Python, but may override some. This is like inheritance in OOP, not taxonomic subsumption.
- **Properties can be negated up the hierarchy**: Python 2 is not backward-compatible with Python 3, so "Python" cannot have a universal property that covers both
- **Installations vs. versions**: a version (Python 3.11) is abstract; an installation is concrete. This distinction matters for licensing, security auditing, etc.
- **Deprecation and end-of-life**: Python 2.7 is a class with existing instances but is deprecated — affects what facts can be inferred

### Special cases

- Operating systems with LTS vs. regular releases (Ubuntu 22.04 LTS)
- Forks: LibreOffice is both an instance of "office suite" and derived from OpenOffice — is it a subclass?
- Open-source vs. proprietary forks with the same name
- APIs as separate from implementations (Python the language vs. CPython the implementation)

---

## How YAGO handles it

TODO

---

## Analysis by formalism

TODO

---

## Why do we need class here?

Without "Python 3.11" as a class:
- Cannot type specific installations as instances
- Cannot express that an installation inherits the version's security vulnerabilities
- Cannot reason: "this installation is Python 3.11, Python 3.11 has CVE-XXXX, therefore this installation is vulnerable"

Without "Python 3.11" as an instance:
- Cannot attach release date, end-of-life date, changelog to the version entity

---

## Questions

- [ ] Does YAGO represent software versions at all, or only the top-level software entity?
- [ ] How does Wikidata model software versions (P348 software version identifier vs. separate items)?
- [ ] Is the version hierarchy better modeled as `rdfs:subClassOf` or as a custom `versionOf` property?
- [ ] How to handle properties that hold for some versions but not others?
