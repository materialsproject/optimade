---
title: '`optimade-python-tools`: a Python library for serving and consuming materials data via OPTIMADE APIs'
tags:
  - Python
  - REST API
  - JSON:API
  - OPTIMADE API
  - crystallography
  - density-functional theory
  - ab initio
  - materials discovery
  - databases
authors:
  - name: Matthew L. Evans
    orcid:  0000-0002-1182-9098
    affiliation: "1, 2"
  - name: Casper W. Andersen
    orcid: 0000-0002-2547-155X
    affiliation: 3
  - name: Shyam Dwaraknath
    orcid: 0000-0003-0289-2607
    affiliation: 4
  - name: Markus Scheidgen
    orcid: 0000-0002-8038-2277
    affiliation: "5, 6"
  - name: Ádám Fekete
    orcid: 0000-0002-6263-897X
    affiliation: "1, 8, 9"
  - name: Donald Winston
    orcid: 0000-0002-8424-0604
    affiliation: "4, 7"
affiliations:
 - name: Institut de la Matière Condensée et des Nanosciences, Université catholique de Louvain, Chemin des Étoiles 8, Louvain-la-Neuve 1348, Belgium
   index: 1
 - name: Theory of Condensed Matter Group, Cavendish Laboratory, University of Cambridge, J. J. Thomson Avenue, Cambridge, CB3 0HE, U.K.
   index: 2
 - name: Theory and Simulation of Materials (THEOS), Faculté des Sciences et Techniques de l'Ingénieur, École Polytechnique Fédérale de Lausanne, CH-1015 Lausanne, Switzerland
   index: 3
 - name: Lawrence Berkeley National Laboratory, Berkeley, CA, USA
   index: 4
 - name: Fritz-Haber-Institut der Max-Planck-Gesellschaft, Faradayweg 4-6, 14195, Berlin, Germany
   index: 5
 - name: Humboldt-Universität zu Berlin, Institut für Physik and IRIS Adlershof, 12489 Berlin, Germany
   index: 6
 - name: Polyneme LLC, New York, NY, USA
   index: 7
 - name: Department of Physics, King's College London, Strand, London WC2R 2LS, United Kingdom
   index: 8
 - name: Department of Physics and Namur Institute of Structured Materials, University of Namur, Rue de Bruxelles 51, 5000 Namur, Belgium
   index: 9

date: June 2021
bibliography: paper.bib
---

# Summary

In recent decades, improvements in algorithms, hardware, and theory have enabled crystalline materials to be studied computationally at the atomistic level with great accuracy and speed.
To enable dissemination, reproducibility, and reuse, many digital crystal structure databases have been created and curated, ready for comparison with existing infrastructure that stores structural characterizations (e.g., diffraction) of real crystals.
These databases have been made available with bespoke application programming interfaces (APIs) to allow for automated and often open access to the underlying data.
Such esoteric and specialized APIs incur maintenance and usability costs upon both the data providers and consumers, who may not be software specialists.

The [OPTIMADE API](https://optimade.org) specification [@andersen2021optimade; @OPTIMADE_spec], released in July 2020, aimed to reduce these costs by designing a common API for use across a consortium of collaborating materials databases and beyond.
Whilst based on the robust JSON:API standard [@JSONAPI], the OPTIMADE API specification presents several domain-specific features and requirements that can be tricky to implement for non-specialist teams.
The repository presented here, `optimade-python-tools`, provides a modular reference server implementation and a set of associated tools to accelerate the development process for data providers, toolmakers and end-users.

# Statement of need

In order to accommodate existing materials database APIs, the OPTIMADE API specification allows for flexibility in the specific data served, but enforces a simple yet domain-specific filter language on well-defined resources.
However, this flexibility could be daunting to database providers, likely acting to increase the barrier to hosting an OPTIMADE REST API.
`optimade-python-tools` aims to catalyse the creation of APIs from existing and new data sources by providing a configurable and modular reference server implementation for hosting materials data in an OPTIMADE-compliant way.
The repository hosts the `optimade` Python package, which leverages the modern Python libraries pydantic [@pydantic] and FastAPI [@FastAPI] to specify the data models and API routes defined in the OPTIMADE API specification, additionally providing a schema following the OpenAPI format [@OpenAPI].
Two storage back-ends are supported out of the box, with full filter support for databases that employ the popular [MongoDB](https://www.mongodb.com) or [Elasticsearch](https://elastic.co) frameworks.

# Functionality

The modular functionality of `optimade` can be broken down by the different stages of a user query to the reference server.
Consider the following query URL to an OPTIMADE API, which should filter for any crystal structures in the database with a composition that consists of any three elements in a 1:1:1 ratio:

```
https://example.org/v1/structures?filter=chemical_formula_anonymous="ABC"
```

1. After routing the query to the appropriate `/structures/` endpoint adhering to version `v1` of the specification, the filter string `chemical_formula_anonymous="ABC"` is tokenized and parsed into an abstract tree by a `FilterParser` object using the Lark parsing library [@Lark] against the formal grammar defined by the specification.
2. The abstract tree is then transformed by a `FilterTransformer` object into a database query specific to the configured back-end for the server.
This transformation can include aliasing and custom transformations such that the underlying database format can be accommodated.
3. The results from the database query are then de-serialized by `EntryResourceMapper` objects into the OPTIMADE-defined data models and finally re-serialized into JSON before being served to the user over HTTP.

Beyond this query functionality, the package also provides:

- A fuzzy implementation validator that performs HTTP queries against remote or local OPTIMADE APIs, with test queries and expected responses generated dynamically based on the data served at the introspective `/info/` endpoint of the API implementation.
- Entry "adapters" that can convert between OPTIMADE-compliant entries and the data models of popular Python libraries used widely in the materials science community: `pymatgen` [@pymatgen], ASE [@ASE], AiiDA [@AiiDA], and JARVIS [@JARVIS].

# Use cases

The package is currently used in production by three major data providers for materials science data:

- The Materials Project [@MaterialsProject] uses `optimade-python-tools` alongside their existing API [@MAPI] and MongoDB database, providing access to highly-curated density-functional theory calculations across all known inorganic materials.
`optimade-python-tools` handles filter parsing, database query generation and response validation by running the reference server implementation with minimal configuration.
- NOMAD [@nomad] uses `optimade-python-tools` as a library to extend its existing web app with OPTIMADE API routes.
 It uses the Elasticsearch implementation to filter millions of structures from published first-principles calculations provided by users and other projects.
NOMAD also uses the filtering module in its own API to expose the OPTIMADE filter language in the user-centric web interface search bar.
NOMAD uses a released version of `optimade-python-tools` and all necessary customization can be realized via configuration and sub-classing.
- Materials Cloud [@MaterialsCloud] uses `optimade-python-tools` as a library to provide an OPTIMADE API entry to archived computational materials studies, created with the AiiDA [@AiiDA] Python framework and published through their archive.
In this case, each individual study and archive entry has its own database and separate API entry.
The Python classes within the `optimade` package have been extended to make use of AiiDA and its underlying [PostgreSQL](https://postgresql.org) storage engine.

# Acknowledgements

All authors acknowledge contributions and feedback from other members of the OPTIMADE consortium, with special thanks to Michael Wu, Leopold Talirz, Thomas Purcell, Abhijith Gopakumar, Andrius Merkys and Fawzi Mohamed for their direct contributions to the `optimade` package.
M.E. would like to acknowledge the EPSRC Centre for Doctoral Training in Computational Methods for Materials Science for funding under grant number EP/L015552/1 and support from the European Union's Horizon 2020 research and innovation program under the European Union's Grant agreement No. 951786 (NOMAD CoE).
C.W.A. acknowledges financial support by the MARKETPLACE project, which is funded by Horizon 2020 under H2020-NMBP-25-2017 call with Grant agreement number: 760173 as well as the National Centres of Competence in Research (NCCR) Materials' revolution: Computational Design and Discovery of Novel Materials (MARVEL) created by the Swiss National Science Foundation (SNSF).
S.D. acknowledges financial support by the U.S. Department of Energy, Office of Science, Office of Basic Energy Sciences, Materials Sciences and Engineering Division under Contract No. DE-AC02-05-CH11231 (Materials Project program KC23MP).
M.S. acknowledges support from the European Union's Horizon 2020 research and innovation program under the European Union's Grant agreement No. 676580 (NoMaD) and No. 951786 (NOMAD CoE) as well as financial support from the Max Planck research network on big-data-driven materials science (BiGmax).
