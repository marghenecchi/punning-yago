# Formalism: RDF / RDFS

## What RDF/RDFS is

RDF (Resource Description Framework) is a graph data model: every statement is a triple `(subject, predicate, object)` where all three components are IRIs (or literals for objects). There is no type system built into RDF itself, everything is just a resource.

RDFS (RDF Schema) adds a minimal vocabulary for describing classes and properties:

| Term                 | Meaning                                                |
| -------------------- | ------------------------------------------------------ |
| `rdf:type`           | membership: `X rdf:type C` means X is an instance of C |
| `rdfs:Class`         | the class of all classes                               |
| `rdfs:subClassOf`    | subset: every instance of A is an instance of B        |
| `rdfs:domain`        | entails type: if `X p Y` then `X rdf:type domain(p)`   |
| `rdfs:range`         | entails type: if `X p Y` then `Y rdf:type range(p)`    |
| `rdfs:subPropertyOf` | property subsumption                                   |

---

## Punning in RDF/RDFS

In RDF, a resource is just an IRI. There is no syntactic or semantic barrier against an IRI appearing both as a class (object of `rdf:type`, subject of `rdfs:subClassOf`) and as an instance (subject of `rdf:type`). The following is valid RDF:

```turtle
ex:Dog  rdf:type        rdfs:Class .       # Dog is a class
ex:Dog  rdfs:subClassOf ex:Animal .        # Dog is a subclass of Animal
ex:Dog  rdf:type        ex:DomesticAnimal. # Dog is an instance of DomesticAnimal
ex:Dog  ex:averageLifespan  "12" .         # Dog has entity-level facts
ex:Rex  rdf:type        ex:Dog .           # Rex is an instance of Dog
```

All five triples are simultaneously valid. RDF/RDFS imposes no constraint that prevents this. Punning is not a problem in RDF, t is the default.

---

## The RDFS metalevel: every class is an instance

RDFS has a built-in metalevel: `rdfs:Class` is the class of all classes. Any entity declared as `rdf:type rdfs:Class` is a class, and every class is automatically an instance of `rdfs:Class`. This is the canonical form of punning in RDFS:

```turtle
ex:Dog  rdf:type  rdfs:Class .   # Dog is a class (and thus an instance of rdfs:Class)
ex:Dog  rdf:type  ex:Animal .    # Dog is also an instance of Animal
```

Moreover, `rdfs:Class` is itself an instance of `rdfs:Class`:

```turtle
rdfs:Class  rdf:type  rdfs:Class .
```

---

## What RDFS semantics say about punning

Under RDFS semantics (defined as a set of entailment rules), the interpretation is purely extensional: a class is any set of resources, and membership is asserted by `rdf:type`. There is no restriction on what can be in a class or what class an individual can belong to.

Key RDFS entailment rules relevant to punning:

| Rule   | Condition                                       | Consequence                     |
| ------ | ----------------------------------------------- | ------------------------------- |
| rdf1   | `aaa rdf:type rdfs:Class`                       | automatic for anything declared |
| rdfs2  | `p rdfs:domain C` and `X p Y`                   | `X rdf:type C`                  |
| rdfs3  | `p rdfs:range C` and `X p Y`                    | `Y rdf:type C`                  |
| rdfs9  | `X rdfs:subClassOf C` and `Y rdf:type X`        | `Y rdf:type C`                  |
| rdfs11 | `A rdfs:subClassOf B` and `B rdfs:subClassOf C` | `A rdfs:subClassOf C`           |

None of these rules distinguish between "X is a class" and "X is an individual". If X is the subject of `rdf:type`, it is an individual. If X is the object of `rdf:type`, it is a class. It can be both.

---

## The problem: domain/range inference across levels

The permissiveness of RDFS creates a specific problem when punning interacts with domain and range inference. Consider:

```turtle
ex:eats  rdfs:domain  ex:Animal .
ex:Dog   ex:eats      ex:Bones .    # generic fact: dogs eat bones
```

RDFS applies rule rdfs2: since `ex:eats rdfs:domain ex:Animal` and `ex:Dog ex:eats ex:Bones`, it infers:

```turtle
ex:Dog  rdf:type  ex:Animal .
```

This is correct if `ex:Dog` is a particular dog (an individual animal). But if `ex:Dog` is a class (the class of all dogs), this inference is wrong: we did not mean that the class Dog is itself an animal, we meant that members of Dog eat bones.

RDFS has no mechanism to distinguish these two readings. The triple `ex:Dog ex:eats ex:Bones` looks identical whether Dog is being treated as an individual or as a stand-in for the kind.

---

## What RDF/RDFS cannot express

| Capability                                                    | RDF/RDFS |
| ------------------------------------------------------------- | -------- |
| Allow entity to be both class and instance                    | ✓        |
| Distinguish "fact about the class" from "fact about the kind" | ✗        |
| Prevent unintended domain/range inferences                    | ✗        |
| Express disjointness between classes                          | ✗        |
| Express cardinality constraints                               | ✗        |
| Separate the class hierarchy from the instance taxonomy       | ✗        |
| Reason about whether a resource is "really" a class           | ✗        |

---

## Punning is invisible in RDF

There is no RDF/RDFS query that separates "triples about Dog as a class" from "triples about Dog as an individual". A SPARQL query for `?x rdf:type ex:Animal` might return Dog (if the domain inference fires) alongside Rex and Tito. There is no standard way to ask "which resources are used as both classes and instances?"

The closest approximation:

```sparql
SELECT ?x WHERE {
  ?x rdf:type rdfs:Class .
  ?x rdf:type ?someClass .
  FILTER (?someClass != rdfs:Class)
}
```

But this would also return any class that has an explicit type annotation for other reasons, and misses cases where the instance role is implicit.

---

## Summary

| Aspect                   | RDF/RDFS behavior                                              |
| ------------------------ | -------------------------------------------------------------- |
| Punning allowed?         | Yes, trivially — no mechanism prevents it                      |
| Punning detected?        | No, no standard vocabulary to mark the distinction             |
| Metalevel punning        | Built-in: every class is an instance of `rdfs:Class`           |
| Inference risk           | Yes: domain/range rules fire on class-level triples            |
| Disambiguation mechanism | None, all left to the application layer                        |
| Relation to YAGO         | YAGO uses RDF as the base layer but resolves punning at ingest |
