# Notes on YAGO

Data problems and observations encountered while working on punning.

## Data problems

- Official website property often resolves to a Wikipedia page in an unexpected language (Elvis)

- Taxon properties not mapped in schema:
  - P183 endemic to
  - P181 — taxon range map image
  - P9566 — diel cycle
  - P9714 — taxon range
  - P7770 — egg incubation period

- BeliefSystem is often not working, maybe try add religion (Q9174)

- Record labels (Q18127) end up under creativeWork instead of Organization, maybe add creative work in record label

- Academic disciplines (mathematics, philosophy, etc.) are fully absent from YAGOso yago:fieldOfWork objects always fail;add a yago:AcademicDiscipline class with ys:fromClass wd:Q11862829, wd:Q4671286?
