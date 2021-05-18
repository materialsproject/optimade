# Changelog

## [v0.14.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.14.1) (2021-05-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.14.0...v0.14.1)

**Fixed bugs:**

- \[SECURITY\] Cycle secrets [\#777](https://github.com/Materials-Consortia/optimade-python-tools/issues/777)

**Closed issues:**

- Do not validate extension endpoints [\#793](https://github.com/Materials-Consortia/optimade-python-tools/issues/793)
- Verify that missing values are not returned in comparisons [\#792](https://github.com/Materials-Consortia/optimade-python-tools/issues/792)

**Merged pull requests:**

- Bump pydantic from 1.8.1 to 1.8.2 [\#805](https://github.com/Materials-Consortia/optimade-python-tools/pull/805) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update GH actions [\#803](https://github.com/Materials-Consortia/optimade-python-tools/pull/803) ([CasperWA](https://github.com/CasperWA))
- Handling null fields in the filtertransformer and validator [\#796](https://github.com/Materials-Consortia/optimade-python-tools/pull/796) ([ml-evs](https://github.com/ml-evs))
- Filter out extension endpoints before validation [\#794](https://github.com/Materials-Consortia/optimade-python-tools/pull/794) ([ml-evs](https://github.com/ml-evs))
- Bump providers from `7a54843` to `fa25ed3` [\#791](https://github.com/Materials-Consortia/optimade-python-tools/pull/791) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump typing-extensions from 3.7.4.3 to 3.10.0.0 [\#789](https://github.com/Materials-Consortia/optimade-python-tools/pull/789) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update dependencies [\#787](https://github.com/Materials-Consortia/optimade-python-tools/pull/787) ([CasperWA](https://github.com/CasperWA))
- Bump CharMixer/auto-changelog-action from v1.2 to v1.3 [\#778](https://github.com/Materials-Consortia/optimade-python-tools/pull/778) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump django from 3.1.7 to 3.1.8 [\#776](https://github.com/Materials-Consortia/optimade-python-tools/pull/776) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update dependencies [\#773](https://github.com/Materials-Consortia/optimade-python-tools/pull/773) ([ml-evs](https://github.com/ml-evs))

## [v0.14.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.14.0) (2021-03-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.3...v0.14.0)

**Implemented enhancements:**

- Rename config variable use\_real\_mongo to something more general [\#742](https://github.com/Materials-Consortia/optimade-python-tools/issues/742)
- Custom configuration extensions & use standard pydantic way of loading config file [\#739](https://github.com/Materials-Consortia/optimade-python-tools/issues/739)
- Generalising collections and adding ElasticsearchCollection [\#660](https://github.com/Materials-Consortia/optimade-python-tools/pull/660) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Over-aggressive middleware to check versioned base URL [\#737](https://github.com/Materials-Consortia/optimade-python-tools/issues/737)
- Floating point comparisons should not be tested with the validator [\#735](https://github.com/Materials-Consortia/optimade-python-tools/issues/735)
- Mapper method `alias_of` extracts alias wrongly [\#667](https://github.com/Materials-Consortia/optimade-python-tools/issues/667)

**Closed issues:**

- Docs builds are not properly tested for each PR [\#747](https://github.com/Materials-Consortia/optimade-python-tools/issues/747)
- Remove SQLAlchemy version fix in CI with new AiiDA version [\#745](https://github.com/Materials-Consortia/optimade-python-tools/issues/745)

**Merged pull requests:**

- Update dependencies [\#760](https://github.com/Materials-Consortia/optimade-python-tools/pull/760) ([CasperWA](https://github.com/CasperWA))
- Fix CheckWronglyVersionedBaseUrls middleware \(for landing pages\) [\#752](https://github.com/Materials-Consortia/optimade-python-tools/pull/752) ([CasperWA](https://github.com/CasperWA))
- Deprecate Python 3.6 support, v0.14 last supported version [\#751](https://github.com/Materials-Consortia/optimade-python-tools/pull/751) ([CasperWA](https://github.com/CasperWA))
- Run full API docs invoke task for every PR [\#748](https://github.com/Materials-Consortia/optimade-python-tools/pull/748) ([ml-evs](https://github.com/ml-evs))
- Change aliasing method names in mapper and deprecate the old [\#746](https://github.com/Materials-Consortia/optimade-python-tools/pull/746) ([ml-evs](https://github.com/ml-evs))
- Bump providers from `e2074e8` to `7a54843` [\#741](https://github.com/Materials-Consortia/optimade-python-tools/pull/741) ([dependabot[bot]](https://github.com/apps/dependabot))
- Config updates [\#740](https://github.com/Materials-Consortia/optimade-python-tools/pull/740) ([CasperWA](https://github.com/CasperWA))
- Disable all floating-point comparisons during validation [\#736](https://github.com/Materials-Consortia/optimade-python-tools/pull/736) ([ml-evs](https://github.com/ml-evs))
- Report user errors in filter as HTTP 400 Bad Request and not 501 Not Implemented [\#658](https://github.com/Materials-Consortia/optimade-python-tools/pull/658) ([markus1978](https://github.com/markus1978))

## [v0.13.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.3) (2021-03-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.2...v0.13.3)

**Fixed bugs:**

- Support `anyOf`, `allOf`, etc. standard OpenAPI fields [\#730](https://github.com/Materials-Consortia/optimade-python-tools/issues/730)
- Python 3.9 support invalid [\#728](https://github.com/Materials-Consortia/optimade-python-tools/issues/728)

**Merged pull requests:**

- Update dependencies [\#734](https://github.com/Materials-Consortia/optimade-python-tools/pull/734) ([CasperWA](https://github.com/CasperWA))
- Update pydantic to ~=1.8 [\#731](https://github.com/Materials-Consortia/optimade-python-tools/pull/731) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `da74513` to `e2074e8` [\#727](https://github.com/Materials-Consortia/optimade-python-tools/pull/727) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.13.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.2) (2021-03-01)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.1...v0.13.2)

**Implemented enhancements:**

- Improve validation of providers [\#723](https://github.com/Materials-Consortia/optimade-python-tools/issues/723)

**Merged pull requests:**

- Update dependencies [\#725](https://github.com/Materials-Consortia/optimade-python-tools/pull/725) ([CasperWA](https://github.com/CasperWA))

## [v0.13.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.1) (2021-02-23)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.0...v0.13.1)

**Fixed bugs:**

- Supported OPTIMADE \_\_api\_version\_\_ is incorrect in latest release [\#712](https://github.com/Materials-Consortia/optimade-python-tools/issues/712)

**Merged pull requests:**

- Bump OPTIMADE version [\#713](https://github.com/Materials-Consortia/optimade-python-tools/pull/713) ([ml-evs](https://github.com/ml-evs))

## [v0.13.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.0) (2021-02-20)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.9...v0.13.0)

**Closed issues:**

- Update species.mass model [\#630](https://github.com/Materials-Consortia/optimade-python-tools/issues/630)

**Merged pull requests:**

- Update species-\>mass field following specification change [\#631](https://github.com/Materials-Consortia/optimade-python-tools/pull/631) ([ml-evs](https://github.com/ml-evs))

## [v0.12.9](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.9) (2021-02-10)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.8...v0.12.9)

**Implemented enhancements:**

- Improve support for timestamp queries in MongoTransformer [\#590](https://github.com/Materials-Consortia/optimade-python-tools/pull/590) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Use Enums for pydantic model defaults instead of strings [\#683](https://github.com/Materials-Consortia/optimade-python-tools/issues/683)

**Closed issues:**

- When using `--as-type` in validator, one does not get a summary \(`--json` doesn't work\) [\#699](https://github.com/Materials-Consortia/optimade-python-tools/issues/699)
- Extension/import issue with mongo collection [\#682](https://github.com/Materials-Consortia/optimade-python-tools/issues/682)

**Merged pull requests:**

- Update dependencies [\#707](https://github.com/Materials-Consortia/optimade-python-tools/pull/707) ([CasperWA](https://github.com/CasperWA))
- Always print summary as last thing in validation [\#700](https://github.com/Materials-Consortia/optimade-python-tools/pull/700) ([CasperWA](https://github.com/CasperWA))
- Bump django from 3.1.5 to 3.1.6 [\#698](https://github.com/Materials-Consortia/optimade-python-tools/pull/698) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update dependencies [\#697](https://github.com/Materials-Consortia/optimade-python-tools/pull/697) ([CasperWA](https://github.com/CasperWA))
- Fixes for new gateway implementation [\#684](https://github.com/Materials-Consortia/optimade-python-tools/pull/684) ([CasperWA](https://github.com/CasperWA))

## [v0.12.8](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.8) (2021-01-18)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.7...v0.12.8)

**Implemented enhancements:**

- Validate mandatory query field `structure_features` [\#678](https://github.com/Materials-Consortia/optimade-python-tools/issues/678)

**Fixed bugs:**

- Validator should not rely on `meta->data_available` [\#677](https://github.com/Materials-Consortia/optimade-python-tools/issues/677)
- Validator should not rely on SHOULD "meta" field "data\_returned" [\#675](https://github.com/Materials-Consortia/optimade-python-tools/issues/675)
- Validator: remove reliance on meta fields and check mandatory queries [\#676](https://github.com/Materials-Consortia/optimade-python-tools/pull/676) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Bump providers from `542ac0a` to `da74513` [\#679](https://github.com/Materials-Consortia/optimade-python-tools/pull/679) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.12.7](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.7) (2021-01-15)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.6...v0.12.7)

**Implemented enhancements:**

- Make content-type response checks on '/versions` endpoint optional [\#670](https://github.com/Materials-Consortia/optimade-python-tools/pull/670) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Publish workflow fails when no changes to api docs between versions [\#673](https://github.com/Materials-Consortia/optimade-python-tools/issues/673)
- /versions header `Content-Type` value should be granularized according to RFC requirements in validator [\#669](https://github.com/Materials-Consortia/optimade-python-tools/issues/669)
- Misleading error message from validator on failure from '/versions' [\#668](https://github.com/Materials-Consortia/optimade-python-tools/issues/668)
- Fix publishing workflow [\#674](https://github.com/Materials-Consortia/optimade-python-tools/pull/674) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Update codecov coverage config file [\#672](https://github.com/Materials-Consortia/optimade-python-tools/pull/672) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `fe5048b` to `542ac0a` [\#671](https://github.com/Materials-Consortia/optimade-python-tools/pull/671) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.12.6](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.6) (2021-01-08)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.5...v0.12.6)

**Implemented enhancements:**

- Create base transformer [\#286](https://github.com/Materials-Consortia/optimade-python-tools/issues/286)

**Fixed bugs:**

- Our models and validator are too strict [\#399](https://github.com/Materials-Consortia/optimade-python-tools/issues/399)
- Validator changes: always check unversioned '/versions' and handle rich HTML pages [\#665](https://github.com/Materials-Consortia/optimade-python-tools/pull/665) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Add more prominent link to rendered docs [\#628](https://github.com/Materials-Consortia/optimade-python-tools/issues/628)
- Review the required properties of StructureResourceAttributes in openapi.json [\#198](https://github.com/Materials-Consortia/optimade-python-tools/issues/198)

**Merged pull requests:**

- Added GitHub CODEOWNERS [\#664](https://github.com/Materials-Consortia/optimade-python-tools/pull/664) ([ml-evs](https://github.com/ml-evs))
- Robustness improvements to validator [\#659](https://github.com/Materials-Consortia/optimade-python-tools/pull/659) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#655](https://github.com/Materials-Consortia/optimade-python-tools/pull/655) ([CasperWA](https://github.com/CasperWA))
- Bugfixes for elasticsearch filtertransformer comparision operators. [\#648](https://github.com/Materials-Consortia/optimade-python-tools/pull/648) ([markus1978](https://github.com/markus1978))
- Update dependencies [\#647](https://github.com/Materials-Consortia/optimade-python-tools/pull/647) ([ml-evs](https://github.com/ml-evs))
- Added "root\_path" config parameter for FastAPI apps [\#634](https://github.com/Materials-Consortia/optimade-python-tools/pull/634) ([markus1978](https://github.com/markus1978))
- Bump providers from `2673be6` to `fe5048b` [\#633](https://github.com/Materials-Consortia/optimade-python-tools/pull/633) ([dependabot[bot]](https://github.com/apps/dependabot))
- Updated README and moved some files to top-level [\#629](https://github.com/Materials-Consortia/optimade-python-tools/pull/629) ([ml-evs](https://github.com/ml-evs))
- insert reading of default optimade\_config.json in example run script run.sh [\#627](https://github.com/Materials-Consortia/optimade-python-tools/pull/627) ([rartino](https://github.com/rartino))
- Create template filtertransformer BaseTransformer [\#287](https://github.com/Materials-Consortia/optimade-python-tools/pull/287) ([ml-evs](https://github.com/ml-evs))

## [v0.12.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.5) (2020-12-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.4...v0.12.5)

**Closed issues:**

- PyPI publishing build is broken by latest pip [\#624](https://github.com/Materials-Consortia/optimade-python-tools/issues/624)
- Empty endpoints raise errors on validation [\#622](https://github.com/Materials-Consortia/optimade-python-tools/issues/622)
- Frequency of updating online docs [\#452](https://github.com/Materials-Consortia/optimade-python-tools/issues/452)

**Merged pull requests:**

- Fix PyPI publishing in CI [\#623](https://github.com/Materials-Consortia/optimade-python-tools/pull/623) ([ml-evs](https://github.com/ml-evs))
- Change validation error to warning on empty endpoints [\#621](https://github.com/Materials-Consortia/optimade-python-tools/pull/621) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#620](https://github.com/Materials-Consortia/optimade-python-tools/pull/620) ([CasperWA](https://github.com/CasperWA))
- Upstream fixes from specification [\#611](https://github.com/Materials-Consortia/optimade-python-tools/pull/611) ([ml-evs](https://github.com/ml-evs))
- Minor fixes for the validator [\#610](https://github.com/Materials-Consortia/optimade-python-tools/pull/610) ([ml-evs](https://github.com/ml-evs))
- Dependency updates [\#607](https://github.com/Materials-Consortia/optimade-python-tools/pull/607) ([ml-evs](https://github.com/ml-evs))
- include LICENSE in pip Package [\#594](https://github.com/Materials-Consortia/optimade-python-tools/pull/594) ([jan-janssen](https://github.com/jan-janssen))
- Relax models to allow for all SHOULD fields to be None [\#560](https://github.com/Materials-Consortia/optimade-python-tools/pull/560) ([ml-evs](https://github.com/ml-evs))
- Python 3.9 support [\#558](https://github.com/Materials-Consortia/optimade-python-tools/pull/558) ([ml-evs](https://github.com/ml-evs))
- ReadTheDocs configuration file \(v2\) [\#485](https://github.com/Materials-Consortia/optimade-python-tools/pull/485) ([CasperWA](https://github.com/CasperWA))

## [v0.12.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.4) (2020-11-16)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.3...v0.12.4)

**Merged pull requests:**

- Minor fixes for versions endpoint validation [\#591](https://github.com/Materials-Consortia/optimade-python-tools/pull/591) ([ml-evs](https://github.com/ml-evs))
- Add --minimal/--page\_limit validator options and remove old code [\#571](https://github.com/Materials-Consortia/optimade-python-tools/pull/571) ([ml-evs](https://github.com/ml-evs))

## [v0.12.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.3) (2020-11-04)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.2...v0.12.3)

**Fixed bugs:**

- GITHUB\_TOKEN not useful for changelog action [\#587](https://github.com/Materials-Consortia/optimade-python-tools/issues/587)
- Hill notation wrong \(still\) [\#585](https://github.com/Materials-Consortia/optimade-python-tools/issues/585)
- Hill notation validation turning around C and H [\#581](https://github.com/Materials-Consortia/optimade-python-tools/issues/581)

**Closed issues:**

- Make structure "deformity" tests more robust [\#583](https://github.com/Materials-Consortia/optimade-python-tools/issues/583)
- Incomplete output of optimade-validator [\#568](https://github.com/Materials-Consortia/optimade-python-tools/issues/568)

**Merged pull requests:**

- Use special release PAT for CHANGELOG generation action [\#588](https://github.com/Materials-Consortia/optimade-python-tools/pull/588) ([CasperWA](https://github.com/CasperWA))
- Check for carbon in elements for Hill [\#586](https://github.com/Materials-Consortia/optimade-python-tools/pull/586) ([CasperWA](https://github.com/CasperWA))
- Added better expected error messages to deformity tests [\#584](https://github.com/Materials-Consortia/optimade-python-tools/pull/584) ([ml-evs](https://github.com/ml-evs))
- Fix Hill ordering validation [\#582](https://github.com/Materials-Consortia/optimade-python-tools/pull/582) ([CasperWA](https://github.com/CasperWA))
- Bump mkdocs-material from 6.1.0 to 6.1.2 [\#580](https://github.com/Materials-Consortia/optimade-python-tools/pull/580) ([dependabot[bot]](https://github.com/apps/dependabot))
- Moved CONFIG import so it does not get triggered when just importing mapper [\#569](https://github.com/Materials-Consortia/optimade-python-tools/pull/569) ([ml-evs](https://github.com/ml-evs))

## [v0.12.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.2) (2020-10-31)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.1...v0.12.2)

**Implemented enhancements:**

- Add convenience method for adding all required middleware [\#536](https://github.com/Materials-Consortia/optimade-python-tools/issues/536)
- Add model validators and regexp for chemical formulae fields [\#547](https://github.com/Materials-Consortia/optimade-python-tools/pull/547) ([ml-evs](https://github.com/ml-evs))
- Validator improvements [\#515](https://github.com/Materials-Consortia/optimade-python-tools/pull/515) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- 'Chosen entry had no value for ...' when property is not requested [\#514](https://github.com/Materials-Consortia/optimade-python-tools/issues/514)
- Fix Species validators and error messages [\#561](https://github.com/Materials-Consortia/optimade-python-tools/pull/561) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Chemical symbols D and T [\#570](https://github.com/Materials-Consortia/optimade-python-tools/issues/570)
- Push back dependabot to monthly updates [\#567](https://github.com/Materials-Consortia/optimade-python-tools/issues/567)
- Spurious validation errors in Structure-\>Species [\#559](https://github.com/Materials-Consortia/optimade-python-tools/issues/559)
- Chemical formulae are not properly validated on model creation [\#546](https://github.com/Materials-Consortia/optimade-python-tools/issues/546)

**Merged pull requests:**

- Update dependencies [\#578](https://github.com/Materials-Consortia/optimade-python-tools/pull/578) ([CasperWA](https://github.com/CasperWA))
- Bump CasperWA/push-protected from v1 to v2.1.0 [\#573](https://github.com/Materials-Consortia/optimade-python-tools/pull/573) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update deps [\#566](https://github.com/Materials-Consortia/optimade-python-tools/pull/566) ([ml-evs](https://github.com/ml-evs))
- Improve handling of MongoDB ObjectID [\#557](https://github.com/Materials-Consortia/optimade-python-tools/pull/557) ([ml-evs](https://github.com/ml-evs))
- Update deps [\#556](https://github.com/Materials-Consortia/optimade-python-tools/pull/556) ([ml-evs](https://github.com/ml-evs))
- Updated dependencies [\#551](https://github.com/Materials-Consortia/optimade-python-tools/pull/551) ([ml-evs](https://github.com/ml-evs))
- Update dependencies - remove black as direct dependency [\#545](https://github.com/Materials-Consortia/optimade-python-tools/pull/545) ([CasperWA](https://github.com/CasperWA))
- Added convenience variables for middleware and exception handlers [\#537](https://github.com/Materials-Consortia/optimade-python-tools/pull/537) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#531](https://github.com/Materials-Consortia/optimade-python-tools/pull/531) ([ml-evs](https://github.com/ml-evs))

## [v0.12.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.1) (2020-09-24)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.0...v0.12.1)

**Implemented enhancements:**

- Move entry schemas to separate submodule [\#511](https://github.com/Materials-Consortia/optimade-python-tools/pull/511) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator should allow implementations to return "501 Not Implemented" for unsupported filters [\#518](https://github.com/Materials-Consortia/optimade-python-tools/issues/518)
- Landing page wrong URL  [\#371](https://github.com/Materials-Consortia/optimade-python-tools/issues/371)

**Merged pull requests:**

- This should ensure requirements\*.txt are tested [\#527](https://github.com/Materials-Consortia/optimade-python-tools/pull/527) ([CasperWA](https://github.com/CasperWA))
- Update dependencies [\#526](https://github.com/Materials-Consortia/optimade-python-tools/pull/526) ([CasperWA](https://github.com/CasperWA))
- Fix landing page URL [\#519](https://github.com/Materials-Consortia/optimade-python-tools/pull/519) ([shyamd](https://github.com/shyamd))
- Update dependencies [\#510](https://github.com/Materials-Consortia/optimade-python-tools/pull/510) ([ml-evs](https://github.com/ml-evs))
- Fixing typo `validatated` -\> `validated` [\#506](https://github.com/Materials-Consortia/optimade-python-tools/pull/506) ([merkys](https://github.com/merkys))
- Make validator respond to KeyboardInterrupts [\#505](https://github.com/Materials-Consortia/optimade-python-tools/pull/505) ([ml-evs](https://github.com/ml-evs))
- Add support levels to validator config [\#503](https://github.com/Materials-Consortia/optimade-python-tools/pull/503) ([ml-evs](https://github.com/ml-evs))
- Enable JSON response from the validator [\#502](https://github.com/Materials-Consortia/optimade-python-tools/pull/502) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#501](https://github.com/Materials-Consortia/optimade-python-tools/pull/501) ([CasperWA](https://github.com/CasperWA))

## [v0.12.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.0) (2020-09-11)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.11.0...v0.12.0)

**Fixed bugs:**

- Missing field descriptions in schema for Species-\>name and Person-\>name [\#492](https://github.com/Materials-Consortia/optimade-python-tools/issues/492)
- "type" field not marked as required for derived entry resource models [\#479](https://github.com/Materials-Consortia/optimade-python-tools/issues/479)
- OpenAPI validations fails due to incorrect type of "dimension\_types" [\#478](https://github.com/Materials-Consortia/optimade-python-tools/issues/478)
- Have fallbacks for retrieving providers list [\#450](https://github.com/Materials-Consortia/optimade-python-tools/issues/450)
- Commit only when necessary [\#495](https://github.com/Materials-Consortia/optimade-python-tools/pull/495) ([CasperWA](https://github.com/CasperWA))
- Fix field optonality inconsistency in schema [\#482](https://github.com/Materials-Consortia/optimade-python-tools/pull/482) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator message for wrong version [\#493](https://github.com/Materials-Consortia/optimade-python-tools/issues/493)
- Validator should validate versions endpoint [\#491](https://github.com/Materials-Consortia/optimade-python-tools/issues/491)
- List of providers not included in `/links` endpoint for index meta-database [\#454](https://github.com/Materials-Consortia/optimade-python-tools/issues/454)
- Validate bad version URLs responding with 553 Version Not Supported [\#427](https://github.com/Materials-Consortia/optimade-python-tools/issues/427)
- Nonexistent property 'list' in validator tests [\#423](https://github.com/Materials-Consortia/optimade-python-tools/issues/423)
- Test `data_returned` [\#402](https://github.com/Materials-Consortia/optimade-python-tools/issues/402)
- AiiDA tests only run on Python 3.8 in CI [\#401](https://github.com/Materials-Consortia/optimade-python-tools/issues/401)
- Links under top-level 'links' may be objects [\#394](https://github.com/Materials-Consortia/optimade-python-tools/issues/394)
- Suggestion: use absolute imports in app code to allow re-use [\#298](https://github.com/Materials-Consortia/optimade-python-tools/issues/298)
- Update mongomock requirement when next released [\#207](https://github.com/Materials-Consortia/optimade-python-tools/issues/207)
- error when browsing OpenAPI docs [\#192](https://github.com/Materials-Consortia/optimade-python-tools/issues/192)

**Merged pull requests:**

- Don't report untracked and ignored files [\#496](https://github.com/Materials-Consortia/optimade-python-tools/pull/496) ([CasperWA](https://github.com/CasperWA))
- Improved error message for bad version returning 553 [\#494](https://github.com/Materials-Consortia/optimade-python-tools/pull/494) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#490](https://github.com/Materials-Consortia/optimade-python-tools/pull/490) ([CasperWA](https://github.com/CasperWA))
- Allow Link objects for pagination [\#484](https://github.com/Materials-Consortia/optimade-python-tools/pull/484) ([ml-evs](https://github.com/ml-evs))
- Absolute imports [\#483](https://github.com/Materials-Consortia/optimade-python-tools/pull/483) ([CasperWA](https://github.com/CasperWA))
- Validate OpenAPI specification in CI [\#481](https://github.com/Materials-Consortia/optimade-python-tools/pull/481) ([ml-evs](https://github.com/ml-evs))
- Update types to align with OpenAPI [\#480](https://github.com/Materials-Consortia/optimade-python-tools/pull/480) ([CasperWA](https://github.com/CasperWA))
- Update dependencies and pre-commit [\#477](https://github.com/Materials-Consortia/optimade-python-tools/pull/477) ([CasperWA](https://github.com/CasperWA))
- Unpin CI Python version for AiiDA tests [\#472](https://github.com/Materials-Consortia/optimade-python-tools/pull/472) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#471](https://github.com/Materials-Consortia/optimade-python-tools/pull/471) ([CasperWA](https://github.com/CasperWA))
- Update dependencies [\#466](https://github.com/Materials-Consortia/optimade-python-tools/pull/466) ([CasperWA](https://github.com/CasperWA))
- Provider list fallback and list of providers in both servers' `/links`-endpoints [\#455](https://github.com/Materials-Consortia/optimade-python-tools/pull/455) ([CasperWA](https://github.com/CasperWA))
- SHOULD/MUST/OPTIONAL fields in models [\#453](https://github.com/Materials-Consortia/optimade-python-tools/pull/453) ([ml-evs](https://github.com/ml-evs))
- Validator overhaul [\#417](https://github.com/Materials-Consortia/optimade-python-tools/pull/417) ([ml-evs](https://github.com/ml-evs))

## [v0.11.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.11.0) (2020-08-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.10.0...v0.11.0)

**Implemented enhancements:**

- Use logging more thoroughly throughout the code base [\#242](https://github.com/Materials-Consortia/optimade-python-tools/issues/242)
- Implement `warnings` [\#105](https://github.com/Materials-Consortia/optimade-python-tools/issues/105)

**Fixed bugs:**

- Heroku is failing - raising OSError when making LOGS\_DIR [\#448](https://github.com/Materials-Consortia/optimade-python-tools/issues/448)
- `/versions` endpoint content-type parameter "header=present" is provided in the wrong place [\#418](https://github.com/Materials-Consortia/optimade-python-tools/issues/418)
- Publish workflow cannot push to protected branch [\#341](https://github.com/Materials-Consortia/optimade-python-tools/issues/341)
- Fix circular dep and extra permission error in logs [\#436](https://github.com/Materials-Consortia/optimade-python-tools/pull/436) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- log\_dir option in config is unused [\#435](https://github.com/Materials-Consortia/optimade-python-tools/issues/435)
- Allow all types of JSON API relationships [\#429](https://github.com/Materials-Consortia/optimade-python-tools/issues/429)
- OPTIMADE version badge was not bumped on 1.0 release [\#415](https://github.com/Materials-Consortia/optimade-python-tools/issues/415)
- Add `api_hint` query parameter [\#392](https://github.com/Materials-Consortia/optimade-python-tools/issues/392)
- Return 553 for wrongly versioned base URLs [\#391](https://github.com/Materials-Consortia/optimade-python-tools/issues/391)
- Private/dunder methods incorrectly documented in mkdocs [\#365](https://github.com/Materials-Consortia/optimade-python-tools/issues/365)
- Configuration documentation [\#310](https://github.com/Materials-Consortia/optimade-python-tools/issues/310)
- Improve handling of sorting in MongoDB backend [\#276](https://github.com/Materials-Consortia/optimade-python-tools/issues/276)

**Merged pull requests:**

- Catch OSError instead of PermissionError when making log dir [\#449](https://github.com/Materials-Consortia/optimade-python-tools/pull/449) ([CasperWA](https://github.com/CasperWA))
- Update dependencies [\#447](https://github.com/Materials-Consortia/optimade-python-tools/pull/447) ([CasperWA](https://github.com/CasperWA))
- Bump mkdocstrings from 0.12.1 to 0.12.2 and mkdocs-material from 5.5.0 to 5.5.2 [\#440](https://github.com/Materials-Consortia/optimade-python-tools/pull/440) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump uvicorn from 0.11.5 to 0.11.7 [\#433](https://github.com/Materials-Consortia/optimade-python-tools/pull/433) ([dependabot[bot]](https://github.com/apps/dependabot))
- Introduce logging [\#432](https://github.com/Materials-Consortia/optimade-python-tools/pull/432) ([CasperWA](https://github.com/CasperWA))
- New middleware to catch any `OptimadeWarning`s [\#431](https://github.com/Materials-Consortia/optimade-python-tools/pull/431) ([CasperWA](https://github.com/CasperWA))
- Auto-generate API reference in docs and an overhaul [\#430](https://github.com/Materials-Consortia/optimade-python-tools/pull/430) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `52027b1` to `9712dd8` [\#428](https://github.com/Materials-Consortia/optimade-python-tools/pull/428) ([dependabot[bot]](https://github.com/apps/dependabot))
- Cleanup config files [\#426](https://github.com/Materials-Consortia/optimade-python-tools/pull/426) ([CasperWA](https://github.com/CasperWA))
- Update more unittest tests to pytest [\#425](https://github.com/Materials-Consortia/optimade-python-tools/pull/425) ([CasperWA](https://github.com/CasperWA))
- Sorting on unknown properties: returning Bad Request when appropriate [\#424](https://github.com/Materials-Consortia/optimade-python-tools/pull/424) ([ml-evs](https://github.com/ml-evs))
- Minor CI updates [\#422](https://github.com/Materials-Consortia/optimade-python-tools/pull/422) ([CasperWA](https://github.com/CasperWA))
- Add `api_hint` query parameter [\#421](https://github.com/Materials-Consortia/optimade-python-tools/pull/421) ([CasperWA](https://github.com/CasperWA))
- Implement 553 Version Not Supported [\#420](https://github.com/Materials-Consortia/optimade-python-tools/pull/420) ([CasperWA](https://github.com/CasperWA))
- Fix incorrect placement of header=present in versions endpoint [\#419](https://github.com/Materials-Consortia/optimade-python-tools/pull/419) ([ml-evs](https://github.com/ml-evs))
- Bump optimade-version.json to 1.0.0 [\#416](https://github.com/Materials-Consortia/optimade-python-tools/pull/416) ([ml-evs](https://github.com/ml-evs))
- Use optimade-validator-action v2 [\#413](https://github.com/Materials-Consortia/optimade-python-tools/pull/413) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `a96d424` to `52027b1` [\#389](https://github.com/Materials-Consortia/optimade-python-tools/pull/389) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.10.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.10.0) (2020-07-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.8...v0.10.0)

**Implemented enhancements:**

- Move tests to pytest system from unittest [\#270](https://github.com/Materials-Consortia/optimade-python-tools/issues/270)

**Fixed bugs:**

- Fix /vMAJOR/info in index server [\#414](https://github.com/Materials-Consortia/optimade-python-tools/pull/414) ([CasperWA](https://github.com/CasperWA))

**Closed issues:**

- Validation of 'structures' type crashes [\#397](https://github.com/Materials-Consortia/optimade-python-tools/issues/397)
- Validator verbosity levels need more detailed description [\#396](https://github.com/Materials-Consortia/optimade-python-tools/issues/396)
- Validator treats top-level 'included' array as mandatory [\#393](https://github.com/Materials-Consortia/optimade-python-tools/issues/393)
- \(Un\)versioned URLs [\#379](https://github.com/Materials-Consortia/optimade-python-tools/issues/379)

**Merged pull requests:**

- Update dependencies [\#412](https://github.com/Materials-Consortia/optimade-python-tools/pull/412) ([CasperWA](https://github.com/CasperWA))
- Bump pydantic from 1.5.1 to 1.6.1 [\#405](https://github.com/Materials-Consortia/optimade-python-tools/pull/405) ([dependabot[bot]](https://github.com/apps/dependabot))
- Temporarily run AiiDA tests on Python 3.8 only [\#400](https://github.com/Materials-Consortia/optimade-python-tools/pull/400) ([ml-evs](https://github.com/ml-evs))
- Make the example for --as\_type more similar to a real use case [\#398](https://github.com/Materials-Consortia/optimade-python-tools/pull/398) ([merkys](https://github.com/merkys))
- Fix some validator-specific crashes [\#395](https://github.com/Materials-Consortia/optimade-python-tools/pull/395) ([ml-evs](https://github.com/ml-evs))
- Use pytest instead of unittest [\#390](https://github.com/Materials-Consortia/optimade-python-tools/pull/390) ([CasperWA](https://github.com/CasperWA))
- Update dependencies [\#388](https://github.com/Materials-Consortia/optimade-python-tools/pull/388) ([CasperWA](https://github.com/CasperWA))

## [v0.9.8](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.8) (2020-07-03)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.7...v0.9.8)

**Implemented enhancements:**

- Set implementation version in config by default [\#385](https://github.com/Materials-Consortia/optimade-python-tools/pull/385) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- Update models, endpoints and responses to 1.0.0 [\#380](https://github.com/Materials-Consortia/optimade-python-tools/pull/380) ([ml-evs](https://github.com/ml-evs))

## [v0.9.7](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.7) (2020-06-28)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.6...v0.9.7)

## [v0.9.6](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.6) (2020-06-28)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.5...v0.9.6)

**Fixed bugs:**

- Fix publish workflow - final\(TM\) fix [\#378](https://github.com/Materials-Consortia/optimade-python-tools/pull/378) ([CasperWA](https://github.com/CasperWA))

## [v0.9.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.5) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.4...v0.9.5)

**Implemented enhancements:**

- Use new action for publishing [\#377](https://github.com/Materials-Consortia/optimade-python-tools/pull/377) ([CasperWA](https://github.com/CasperWA))

## [v0.9.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.4) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.3...v0.9.4)

## [v0.9.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.3) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.2...v0.9.3)

**Merged pull requests:**

- Fix version issues in the publish workflow [\#376](https://github.com/Materials-Consortia/optimade-python-tools/pull/376) ([shyamd](https://github.com/shyamd))
- Bump providers from `732593a` to `a96d424` [\#368](https://github.com/Materials-Consortia/optimade-python-tools/pull/368) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.9.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.2) (2020-06-25)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.1...v0.9.2)

**Fixed bugs:**

- Heroku cannot handle submodules when deploying via GitHub [\#373](https://github.com/Materials-Consortia/optimade-python-tools/issues/373)

**Closed issues:**

- Updates to models \(new OPTIONAL `type` field under `properties`\) [\#345](https://github.com/Materials-Consortia/optimade-python-tools/issues/345)
- Add aggregatation fields to links model [\#344](https://github.com/Materials-Consortia/optimade-python-tools/issues/344)
- Updates to models \(nperiodic\_dimensions\) [\#343](https://github.com/Materials-Consortia/optimade-python-tools/issues/343)
- Updates to models \(changing unknown atoms\) [\#342](https://github.com/Materials-Consortia/optimade-python-tools/issues/342)
- Improvements/fixes for openapi.json [\#332](https://github.com/Materials-Consortia/optimade-python-tools/issues/332)
- Update to v1.0.0-rc.1 [\#329](https://github.com/Materials-Consortia/optimade-python-tools/issues/329)
- Decouple updates in providers repo [\#311](https://github.com/Materials-Consortia/optimade-python-tools/issues/311)
- RST not rendering with mkdocs [\#307](https://github.com/Materials-Consortia/optimade-python-tools/issues/307)

**Merged pull requests:**

- Retrieve providers list if no submodule is found [\#374](https://github.com/Materials-Consortia/optimade-python-tools/pull/374) ([CasperWA](https://github.com/CasperWA))
- Update default implementation information [\#372](https://github.com/Materials-Consortia/optimade-python-tools/pull/372) ([shyamd](https://github.com/shyamd))
- Bump spec version to 1.0.0-rc.2 [\#367](https://github.com/Materials-Consortia/optimade-python-tools/pull/367) ([ml-evs](https://github.com/ml-evs))
- Dependabot updates: numpy, mkdocs-material, mkdocstrings, requests [\#364](https://github.com/Materials-Consortia/optimade-python-tools/pull/364) ([ml-evs](https://github.com/ml-evs))
- Merge all Dependabot updates [\#353](https://github.com/Materials-Consortia/optimade-python-tools/pull/353) ([shyamd](https://github.com/shyamd))
- Update model descriptions and openapi.json for 1.0.0-rc2 [\#351](https://github.com/Materials-Consortia/optimade-python-tools/pull/351) ([ml-evs](https://github.com/ml-evs))
- Update models according to changes during CECAM 2020 meeting [\#350](https://github.com/Materials-Consortia/optimade-python-tools/pull/350) ([ml-evs](https://github.com/ml-evs))
- Decouple changes in providers repo [\#312](https://github.com/Materials-Consortia/optimade-python-tools/pull/312) ([shyamd](https://github.com/shyamd))

## [v0.9.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.1) (2020-06-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.0...v0.9.1)

## [v0.9.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.0) (2020-06-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.8.1...v0.9.0)

**Implemented enhancements:**

- Breaking up the python tools into seperable packages [\#255](https://github.com/Materials-Consortia/optimade-python-tools/issues/255)
- Run both servers as standard [\#238](https://github.com/Materials-Consortia/optimade-python-tools/issues/238)

**Fixed bugs:**

- Non-running CI job [\#331](https://github.com/Materials-Consortia/optimade-python-tools/issues/331)
- Special species "X" not tested for non-disordered structures [\#304](https://github.com/Materials-Consortia/optimade-python-tools/issues/304)
- Standardize timezone of datetime responses [\#288](https://github.com/Materials-Consortia/optimade-python-tools/issues/288)
- Queries on aliased/provider fields are broken for nested properties [\#282](https://github.com/Materials-Consortia/optimade-python-tools/issues/282)
- General exceptions not being put into response [\#281](https://github.com/Materials-Consortia/optimade-python-tools/issues/281)
- Issue with CIF export [\#271](https://github.com/Materials-Consortia/optimade-python-tools/issues/271)
- Type-cast inputs for general Error [\#280](https://github.com/Materials-Consortia/optimade-python-tools/pull/280) ([CasperWA](https://github.com/CasperWA))

**Security fixes:**

- \[Security\] Bump django from 3.0.4 to 3.0.7 in /.github/workflows [\#291](https://github.com/Materials-Consortia/optimade-python-tools/pull/291) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))

**Closed issues:**

- Update links resources [\#299](https://github.com/Materials-Consortia/optimade-python-tools/issues/299)
- Need to set up mkdocs [\#289](https://github.com/Materials-Consortia/optimade-python-tools/issues/289)
- Need to add custom schema entries for unit/sortable \(and eventually type\) [\#278](https://github.com/Materials-Consortia/optimade-python-tools/issues/278)
- /info/\<entry-endpoint\> missing `sortable` key under each property [\#273](https://github.com/Materials-Consortia/optimade-python-tools/issues/273)
- Make CI linting more useful [\#269](https://github.com/Materials-Consortia/optimade-python-tools/issues/269)
- \[PR SPECIFIC\] Reminder: Validator test pinned to specific commit [\#268](https://github.com/Materials-Consortia/optimade-python-tools/issues/268)
- Validator does not check that pagination links work [\#265](https://github.com/Materials-Consortia/optimade-python-tools/issues/265)
- available\_api\_versions is not correctly validated [\#261](https://github.com/Materials-Consortia/optimade-python-tools/issues/261)
- Implementation model should allow for any URL type in `source_url` [\#260](https://github.com/Materials-Consortia/optimade-python-tools/issues/260)
- Extra structure endpoints in the api specification @ odbx [\#259](https://github.com/Materials-Consortia/optimade-python-tools/issues/259)
- Wrong response structure at info endpoint @ cod [\#258](https://github.com/Materials-Consortia/optimade-python-tools/issues/258)
- Missing base url for api's docs @ materialscloud [\#257](https://github.com/Materials-Consortia/optimade-python-tools/issues/257)
- Handling of KNOWN in mongo backend [\#254](https://github.com/Materials-Consortia/optimade-python-tools/issues/254)
- `None` values in `lattice_vectors` [\#170](https://github.com/Materials-Consortia/optimade-python-tools/issues/170)
- Make sure that the PyPI distribution works [\#143](https://github.com/Materials-Consortia/optimade-python-tools/issues/143)
- Move run.sh to a python file to be environment-agnostic [\#81](https://github.com/Materials-Consortia/optimade-python-tools/issues/81)

**Merged pull requests:**

- Another fix for release pipeline [\#355](https://github.com/Materials-Consortia/optimade-python-tools/pull/355) ([shyamd](https://github.com/shyamd))
- Fix publish workflow [\#354](https://github.com/Materials-Consortia/optimade-python-tools/pull/354) ([CasperWA](https://github.com/CasperWA))
- Fix publish workflow [\#352](https://github.com/Materials-Consortia/optimade-python-tools/pull/352) ([CasperWA](https://github.com/CasperWA))
- Update publish workflow [\#340](https://github.com/Materials-Consortia/optimade-python-tools/pull/340) ([shyamd](https://github.com/shyamd))
- Remove test publish action [\#338](https://github.com/Materials-Consortia/optimade-python-tools/pull/338) ([shyamd](https://github.com/shyamd))
- Fix 'publish\_TestPyPI' CI job [\#337](https://github.com/Materials-Consortia/optimade-python-tools/pull/337) ([CasperWA](https://github.com/CasperWA))
- Specify versions for all setup.py deps [\#336](https://github.com/Materials-Consortia/optimade-python-tools/pull/336) ([CasperWA](https://github.com/CasperWA))
- Represent the datetime objects as UTC in RFC3339 format [\#333](https://github.com/Materials-Consortia/optimade-python-tools/pull/333) ([fekad](https://github.com/fekad))
- dependamat: Bump \<package\_name\> v x.y.z to vx.y.\(z+1\) [\#330](https://github.com/Materials-Consortia/optimade-python-tools/pull/330) ([ml-evs](https://github.com/ml-evs))
- Bump fastapi from 0.53.1 to 0.56.0 [\#324](https://github.com/Materials-Consortia/optimade-python-tools/pull/324) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump pydantic from 1.4 to 1.5.1 [\#320](https://github.com/Materials-Consortia/optimade-python-tools/pull/320) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update links resources [\#306](https://github.com/Materials-Consortia/optimade-python-tools/pull/306) ([CasperWA](https://github.com/CasperWA))
- Add special species for adapters testing [\#305](https://github.com/Materials-Consortia/optimade-python-tools/pull/305) ([CasperWA](https://github.com/CasperWA))
- Clean Up Build Environment [\#301](https://github.com/Materials-Consortia/optimade-python-tools/pull/301) ([shyamd](https://github.com/shyamd))
- Enable CI failures for linting [\#300](https://github.com/Materials-Consortia/optimade-python-tools/pull/300) ([ml-evs](https://github.com/ml-evs))
- Adding jarvis-tools structures [\#297](https://github.com/Materials-Consortia/optimade-python-tools/pull/297) ([knc6](https://github.com/knc6))
- Update Docs [\#295](https://github.com/Materials-Consortia/optimade-python-tools/pull/295) ([shyamd](https://github.com/shyamd))
- Setup MKDocs for Documentation [\#294](https://github.com/Materials-Consortia/optimade-python-tools/pull/294) ([shyamd](https://github.com/shyamd))
- Fix filters on nested provider/aliased fields [\#285](https://github.com/Materials-Consortia/optimade-python-tools/pull/285) ([ml-evs](https://github.com/ml-evs))
- Use heroku-shields instead of heroku-badge [\#284](https://github.com/Materials-Consortia/optimade-python-tools/pull/284) ([CasperWA](https://github.com/CasperWA))
- Add OPTIMADE logo to badge by extending JSON [\#283](https://github.com/Materials-Consortia/optimade-python-tools/pull/283) ([CasperWA](https://github.com/CasperWA))
- Add null check to mongo filtertransformer for KNOWN/UNKNOWN filters [\#279](https://github.com/Materials-Consortia/optimade-python-tools/pull/279) ([ml-evs](https://github.com/ml-evs))
- Add `sortable=True` to all properties [\#274](https://github.com/Materials-Consortia/optimade-python-tools/pull/274) ([CasperWA](https://github.com/CasperWA))
- Make \_atom\_site\_label unique in CIF generation [\#272](https://github.com/Materials-Consortia/optimade-python-tools/pull/272) ([CasperWA](https://github.com/CasperWA))
- Not so quick fix to allow "/" at end of validator URL, plus fixes and tests for --as\_type [\#267](https://github.com/Materials-Consortia/optimade-python-tools/pull/267) ([ml-evs](https://github.com/ml-evs))
- Check pagination links-\>next with validator [\#266](https://github.com/Materials-Consortia/optimade-python-tools/pull/266) ([ml-evs](https://github.com/ml-evs))
- Relax HTTP URL constraints on meta-\>implementation-\>source\_url field. [\#262](https://github.com/Materials-Consortia/optimade-python-tools/pull/262) ([ml-evs](https://github.com/ml-evs))
- Validate lattice\_vectors for all null or all float [\#171](https://github.com/Materials-Consortia/optimade-python-tools/pull/171) ([CasperWA](https://github.com/CasperWA))

## [v0.8.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.8.1) (2020-04-25)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.8.0...v0.8.1)

**Fixed bugs:**

- Pip install missing some files [\#252](https://github.com/Materials-Consortia/optimade-python-tools/issues/252)

**Merged pull requests:**

- v0.8.1 hotfix [\#256](https://github.com/Materials-Consortia/optimade-python-tools/pull/256) ([ml-evs](https://github.com/ml-evs))
- Fix 252 missing landing page [\#253](https://github.com/Materials-Consortia/optimade-python-tools/pull/253) ([shyamd](https://github.com/shyamd))

## [v0.8.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.8.0) (2020-04-22)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.7.1...v0.8.0)

**Implemented enhancements:**

- Switch to pydantic's BaseSettings for the config file? [\#152](https://github.com/Materials-Consortia/optimade-python-tools/issues/152)
- Use services for testing/updating dependencies? [\#96](https://github.com/Materials-Consortia/optimade-python-tools/issues/96)
- Remove query constraints for /links-endpoint [\#244](https://github.com/Materials-Consortia/optimade-python-tools/pull/244) ([CasperWA](https://github.com/CasperWA))
- Add adapters - Base design + 'structures' \(+ 'references'... sort of\) [\#241](https://github.com/Materials-Consortia/optimade-python-tools/pull/241) ([CasperWA](https://github.com/CasperWA))
- Add dependabot and last commit date badges [\#237](https://github.com/Materials-Consortia/optimade-python-tools/pull/237) ([CasperWA](https://github.com/CasperWA))
- Add mongo length operator functionality with length aliases [\#222](https://github.com/Materials-Consortia/optimade-python-tools/pull/222) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Use Path.home\(\) instead of ~ in default config path values [\#245](https://github.com/Materials-Consortia/optimade-python-tools/issues/245)

**Closed issues:**

- Have Dependabot take care of various requirements.txt files as well [\#249](https://github.com/Materials-Consortia/optimade-python-tools/issues/249)
- Remove commented out GH Action job `deps_clean-install` [\#247](https://github.com/Materials-Consortia/optimade-python-tools/issues/247)
- Local testing fails without default config [\#239](https://github.com/Materials-Consortia/optimade-python-tools/issues/239)
- Release only when pushing to master [\#229](https://github.com/Materials-Consortia/optimade-python-tools/issues/229)
- Do we need `server.cfg`? [\#134](https://github.com/Materials-Consortia/optimade-python-tools/issues/134)
- Implement LENGTH in query [\#86](https://github.com/Materials-Consortia/optimade-python-tools/issues/86)

**Merged pull requests:**

- Up to v0.8.0 [\#251](https://github.com/Materials-Consortia/optimade-python-tools/pull/251) ([CasperWA](https://github.com/CasperWA))
- Remove old commented GH Action job [\#250](https://github.com/Materials-Consortia/optimade-python-tools/pull/250) ([CasperWA](https://github.com/CasperWA))
- Use Path.home\(\) instead of `~` [\#246](https://github.com/Materials-Consortia/optimade-python-tools/pull/246) ([CasperWA](https://github.com/CasperWA))
- Fix path in default config [\#243](https://github.com/Materials-Consortia/optimade-python-tools/pull/243) ([ml-evs](https://github.com/ml-evs))
- Fixes Local Tests [\#240](https://github.com/Materials-Consortia/optimade-python-tools/pull/240) ([shyamd](https://github.com/shyamd))
- Revert "Fix github actions for non-release tags" [\#236](https://github.com/Materials-Consortia/optimade-python-tools/pull/236) ([shyamd](https://github.com/shyamd))
- Enable filtering on relationships with mongo  [\#234](https://github.com/Materials-Consortia/optimade-python-tools/pull/234) ([ml-evs](https://github.com/ml-evs))
- Update filter examples and validate optional cases [\#227](https://github.com/Materials-Consortia/optimade-python-tools/pull/227) ([ml-evs](https://github.com/ml-evs))
- Switch from config init to BaseSettings [\#226](https://github.com/Materials-Consortia/optimade-python-tools/pull/226) ([shyamd](https://github.com/shyamd))

## [v0.7.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.7.1) (2020-03-16)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.7.0...v0.7.1)

**Closed issues:**

- Fix all capitalisation of OPTIMADE [\#232](https://github.com/Materials-Consortia/optimade-python-tools/issues/232)
- Remove validator action from README [\#230](https://github.com/Materials-Consortia/optimade-python-tools/issues/230)

**Merged pull requests:**

- Fix github actions for non-release tags [\#235](https://github.com/Materials-Consortia/optimade-python-tools/pull/235) ([shyamd](https://github.com/shyamd))
- Update OPTIMADE capitalisation [\#233](https://github.com/Materials-Consortia/optimade-python-tools/pull/233) ([ml-evs](https://github.com/ml-evs))
- Update mentions of action in readme [\#231](https://github.com/Materials-Consortia/optimade-python-tools/pull/231) ([ml-evs](https://github.com/ml-evs))

## [v0.7.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.7.0) (2020-03-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.6.0...v0.7.0)

**Implemented enhancements:**

- Validate all non-optional :filter: examples from the spec [\#213](https://github.com/Materials-Consortia/optimade-python-tools/pull/213) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Some mandatory filter examples from spec do not work [\#217](https://github.com/Materials-Consortia/optimade-python-tools/issues/217)
- Add txt-files in optimade.validator.data to MANIFEST [\#225](https://github.com/Materials-Consortia/optimade-python-tools/pull/225) ([CasperWA](https://github.com/CasperWA))
- Handle arbitrary nested NOT/AND/OR in queries [\#221](https://github.com/Materials-Consortia/optimade-python-tools/pull/221) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator only validates what we have working, not what is required by the spec [\#182](https://github.com/Materials-Consortia/optimade-python-tools/issues/182)

**Merged pull requests:**

- v0.7.0 release [\#228](https://github.com/Materials-Consortia/optimade-python-tools/pull/228) ([ml-evs](https://github.com/ml-evs))
- Remove GH Action to validate OPTiMaDe instances [\#224](https://github.com/Materials-Consortia/optimade-python-tools/pull/224) ([CasperWA](https://github.com/CasperWA))
- Codecov-action supports token-less uploads [\#220](https://github.com/Materials-Consortia/optimade-python-tools/pull/220) ([CasperWA](https://github.com/CasperWA))
- Update django requirement from \>=2.2.9,~=2.2 to \>=2.2,\<4.0 [\#219](https://github.com/Materials-Consortia/optimade-python-tools/pull/219) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))
- Update elasticsearch-dsl requirement from ~=6.4 to \>=6.4,\<8.0 [\#218](https://github.com/Materials-Consortia/optimade-python-tools/pull/218) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))

## [v0.6.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.6.0) (2020-03-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.5.0...v0.6.0)

**Implemented enhancements:**

- Possibly add CORS middleware [\#159](https://github.com/Materials-Consortia/optimade-python-tools/issues/159)
- Add debug flag to server [\#130](https://github.com/Materials-Consortia/optimade-python-tools/issues/130)
- Make validator GitHub Action [\#191](https://github.com/Materials-Consortia/optimade-python-tools/pull/191) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- meta/query/representation value not cutting off version properly [\#199](https://github.com/Materials-Consortia/optimade-python-tools/issues/199)
- URL for providers.json from Materials-Consortia has changed [\#186](https://github.com/Materials-Consortia/optimade-python-tools/issues/186)
- Relationships don't work when "/" present in id [\#181](https://github.com/Materials-Consortia/optimade-python-tools/issues/181)
- Redirect middleware not hitting single-entry endpoints [\#174](https://github.com/Materials-Consortia/optimade-python-tools/issues/174)

**Closed issues:**

- /info/ reports wrong url under available\_api\_versions [\#215](https://github.com/Materials-Consortia/optimade-python-tools/issues/215)
- Query parameters not handled correctly [\#208](https://github.com/Materials-Consortia/optimade-python-tools/issues/208)
- Test for AvailableApiVersion is correct for the wrong reasons [\#204](https://github.com/Materials-Consortia/optimade-python-tools/issues/204)
- Drop '/optimade' from paths in openapi.json [\#197](https://github.com/Materials-Consortia/optimade-python-tools/issues/197)
- heroku is failing [\#185](https://github.com/Materials-Consortia/optimade-python-tools/issues/185)
- List properties and HAS \_ operators missing [\#98](https://github.com/Materials-Consortia/optimade-python-tools/issues/98)
- Checklist for OPTiMaDe v0.10.1 [\#29](https://github.com/Materials-Consortia/optimade-python-tools/issues/29)

**Merged pull requests:**

- Removed /optimade/ prefix in info response [\#216](https://github.com/Materials-Consortia/optimade-python-tools/pull/216) ([ml-evs](https://github.com/ml-evs))
- Self load data [\#212](https://github.com/Materials-Consortia/optimade-python-tools/pull/212) ([shyamd](https://github.com/shyamd))
- Update tests for available\_api\_versions [\#211](https://github.com/Materials-Consortia/optimade-python-tools/pull/211) ([CasperWA](https://github.com/CasperWA))
- Up to v0.6.0 [\#210](https://github.com/Materials-Consortia/optimade-python-tools/pull/210) ([CasperWA](https://github.com/CasperWA))
- Update handling of include parameter \(and other query parameters\) [\#209](https://github.com/Materials-Consortia/optimade-python-tools/pull/209) ([CasperWA](https://github.com/CasperWA))
- Skip HAS ONLY test if mongomock version \<= 3.19.0 [\#206](https://github.com/Materials-Consortia/optimade-python-tools/pull/206) ([ml-evs](https://github.com/ml-evs))
- Test mandatory queries in validator [\#205](https://github.com/Materials-Consortia/optimade-python-tools/pull/205) ([ml-evs](https://github.com/ml-evs))
- Fix include query parameter [\#202](https://github.com/Materials-Consortia/optimade-python-tools/pull/202) ([CasperWA](https://github.com/CasperWA))
- Fix meta.query.representation and remove /optimade in base URLs [\#201](https://github.com/Materials-Consortia/optimade-python-tools/pull/201) ([CasperWA](https://github.com/CasperWA))
- Use mongo for CI [\#196](https://github.com/Materials-Consortia/optimade-python-tools/pull/196) ([ml-evs](https://github.com/ml-evs))
- \(Cosmetic\) updates to models [\#195](https://github.com/Materials-Consortia/optimade-python-tools/pull/195) ([CasperWA](https://github.com/CasperWA))
- Add CORSMiddleware [\#194](https://github.com/Materials-Consortia/optimade-python-tools/pull/194) ([CasperWA](https://github.com/CasperWA))
- Add "debug mode" [\#190](https://github.com/Materials-Consortia/optimade-python-tools/pull/190) ([CasperWA](https://github.com/CasperWA))
- Use https://provider.optimade.org/providers.json [\#187](https://github.com/Materials-Consortia/optimade-python-tools/pull/187) ([CasperWA](https://github.com/CasperWA))
- Fix errors parsing IDs that contain slashes [\#183](https://github.com/Materials-Consortia/optimade-python-tools/pull/183) ([ml-evs](https://github.com/ml-evs))
- Added default mongo implementations for HAS ALL/ANY/ONLY [\#173](https://github.com/Materials-Consortia/optimade-python-tools/pull/173) ([ml-evs](https://github.com/ml-evs))

## [v0.5.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.5.0) (2020-02-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.4.0...v0.5.0)

**Implemented enhancements:**

- Implement a landing page for requests to the base URL [\#169](https://github.com/Materials-Consortia/optimade-python-tools/issues/169)

**Fixed bugs:**

- 'minor' and 'patch' versioned base URL prefixes are wrong [\#177](https://github.com/Materials-Consortia/optimade-python-tools/issues/177)

**Closed issues:**

- Handle `include` standard JSON API query parameter [\#94](https://github.com/Materials-Consortia/optimade-python-tools/issues/94)

**Merged pull requests:**

- Bump to v0.5.0 [\#179](https://github.com/Materials-Consortia/optimade-python-tools/pull/179) ([CasperWA](https://github.com/CasperWA))
- Correctly create optional versioned base URLs [\#178](https://github.com/Materials-Consortia/optimade-python-tools/pull/178) ([CasperWA](https://github.com/CasperWA))
- Make mapper aliases configurable [\#175](https://github.com/Materials-Consortia/optimade-python-tools/pull/175) ([ml-evs](https://github.com/ml-evs))
- Add landing page at base URL [\#172](https://github.com/Materials-Consortia/optimade-python-tools/pull/172) ([ml-evs](https://github.com/ml-evs))
- Implement `include` query parameter [\#163](https://github.com/Materials-Consortia/optimade-python-tools/pull/163) ([CasperWA](https://github.com/CasperWA))
- Add docker for index meta-database [\#140](https://github.com/Materials-Consortia/optimade-python-tools/pull/140) ([CasperWA](https://github.com/CasperWA))

## [v0.4.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.4.0) (2020-02-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.4...v0.4.0)

**Implemented enhancements:**

- switch to pipenv? [\#37](https://github.com/Materials-Consortia/optimade-python-tools/issues/37)
- Reorder tests [\#162](https://github.com/Materials-Consortia/optimade-python-tools/pull/162) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Server app intermingles [\#161](https://github.com/Materials-Consortia/optimade-python-tools/issues/161)
- `response_fields` not working [\#154](https://github.com/Materials-Consortia/optimade-python-tools/issues/154)

**Closed issues:**

- Change `page_page` to `page_number` [\#165](https://github.com/Materials-Consortia/optimade-python-tools/issues/165)
- Add schema-relevant parameters to query parameters [\#164](https://github.com/Materials-Consortia/optimade-python-tools/issues/164)
- Alias optimade/structures/ to optimade/structure [\#128](https://github.com/Materials-Consortia/optimade-python-tools/issues/128)
- Minor changes to specification v0.10.1-develop [\#115](https://github.com/Materials-Consortia/optimade-python-tools/issues/115)
- Update models with new levels of REQUIRED response properties [\#114](https://github.com/Materials-Consortia/optimade-python-tools/issues/114)
- Constraining list/array types in the schema [\#55](https://github.com/Materials-Consortia/optimade-python-tools/issues/55)

**Merged pull requests:**

- Bump to v0.4.0 [\#168](https://github.com/Materials-Consortia/optimade-python-tools/pull/168) ([CasperWA](https://github.com/CasperWA))
- Describe query parameters in OpenAPI schema [\#166](https://github.com/Materials-Consortia/optimade-python-tools/pull/166) ([CasperWA](https://github.com/CasperWA))
- Redirect slashed URLs [\#160](https://github.com/Materials-Consortia/optimade-python-tools/pull/160) ([CasperWA](https://github.com/CasperWA))
- New REQUIRED level properties [\#153](https://github.com/Materials-Consortia/optimade-python-tools/pull/153) ([CasperWA](https://github.com/CasperWA))

## [v0.3.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.4) (2020-02-04)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.3...v0.3.4)

**Implemented enhancements:**

- Include `develop` or not? Default branch? - Create INSTALL.md [\#136](https://github.com/Materials-Consortia/optimade-python-tools/issues/136)

**Fixed bugs:**

- Excepting non-existent exception [\#129](https://github.com/Materials-Consortia/optimade-python-tools/issues/129)

**Closed issues:**

- disable serving API under /v0.10 and /v0.10.0 by default? [\#122](https://github.com/Materials-Consortia/optimade-python-tools/issues/122)
- PyPI release checklist [\#67](https://github.com/Materials-Consortia/optimade-python-tools/issues/67)

**Merged pull requests:**

- Bump to v0.3.4 [\#158](https://github.com/Materials-Consortia/optimade-python-tools/pull/158) ([CasperWA](https://github.com/CasperWA))
- Fix heroku badge [\#157](https://github.com/Materials-Consortia/optimade-python-tools/pull/157) ([ml-evs](https://github.com/ml-evs))
- Move installation instructions [\#156](https://github.com/Materials-Consortia/optimade-python-tools/pull/156) ([ml-evs](https://github.com/ml-evs))
- Update base URLs [\#155](https://github.com/Materials-Consortia/optimade-python-tools/pull/155) ([CasperWA](https://github.com/CasperWA))
- Extend OpenAPI/spec description [\#151](https://github.com/Materials-Consortia/optimade-python-tools/pull/151) ([CasperWA](https://github.com/CasperWA))
- Non Local Mongo [\#150](https://github.com/Materials-Consortia/optimade-python-tools/pull/150) ([shyamd](https://github.com/shyamd))

## [v0.3.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.3) (2020-01-24)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.2...v0.3.3)

**Fixed bugs:**

- Lark files not being distributed [\#141](https://github.com/Materials-Consortia/optimade-python-tools/issues/141)

**Closed issues:**

- Tests fail with lark-parser\>=0.8 [\#146](https://github.com/Materials-Consortia/optimade-python-tools/issues/146)

**Merged pull requests:**

- Updated lark-parser to 0.8.1 [\#149](https://github.com/Materials-Consortia/optimade-python-tools/pull/149) ([ml-evs](https://github.com/ml-evs))
- Split eager and standard tests to avoid unnecessary badge of shame [\#148](https://github.com/Materials-Consortia/optimade-python-tools/pull/148) ([ml-evs](https://github.com/ml-evs))
- Bump to v0.3.3 [\#147](https://github.com/Materials-Consortia/optimade-python-tools/pull/147) ([CasperWA](https://github.com/CasperWA))
- Fix root\_validator issues with optional fields and made meta optional [\#145](https://github.com/Materials-Consortia/optimade-python-tools/pull/145) ([ml-evs](https://github.com/ml-evs))
- Handle `JSONDecodeError`s in validator [\#144](https://github.com/Materials-Consortia/optimade-python-tools/pull/144) ([ml-evs](https://github.com/ml-evs))

## [v0.3.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.2) (2020-01-20)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.1...v0.3.2)

**Implemented enhancements:**

- Add base URL to configuration file [\#135](https://github.com/Materials-Consortia/optimade-python-tools/pull/135) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Fix `load_from_json` [\#137](https://github.com/Materials-Consortia/optimade-python-tools/pull/137) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- Make sure relevant package data is included in distributions [\#142](https://github.com/Materials-Consortia/optimade-python-tools/pull/142) ([CasperWA](https://github.com/CasperWA))
- Add database page limit [\#139](https://github.com/Materials-Consortia/optimade-python-tools/pull/139) ([CasperWA](https://github.com/CasperWA))

## [v0.3.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.1) (2020-01-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.0...v0.3.1)

**Merged pull requests:**

- Update requirements [\#138](https://github.com/Materials-Consortia/optimade-python-tools/pull/138) ([CasperWA](https://github.com/CasperWA))

## [v0.3.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.0) (2020-01-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.2...v0.3.0)

**Implemented enhancements:**

- Implement optional `implementation` in top-level meta response [\#117](https://github.com/Materials-Consortia/optimade-python-tools/issues/117)
- Create "special" index meta-database server [\#100](https://github.com/Materials-Consortia/optimade-python-tools/issues/100)
- Implement relationships in server [\#71](https://github.com/Materials-Consortia/optimade-python-tools/issues/71)
- Add missing /references endpoint to server [\#69](https://github.com/Materials-Consortia/optimade-python-tools/issues/69)
- Automatically publish version tags to PyPI via GH Actions [\#107](https://github.com/Materials-Consortia/optimade-python-tools/pull/107) ([CasperWA](https://github.com/CasperWA))
- Using routers [\#99](https://github.com/Materials-Consortia/optimade-python-tools/pull/99) ([CasperWA](https://github.com/CasperWA))
- Add relationships functionality [\#91](https://github.com/Materials-Consortia/optimade-python-tools/pull/91) ([ml-evs](https://github.com/ml-evs))
- Added external API validator based on our pydantic models [\#74](https://github.com/Materials-Consortia/optimade-python-tools/pull/74) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- The invoke task `update-openapijson` is incomplete [\#123](https://github.com/Materials-Consortia/optimade-python-tools/issues/123)
- Django vulnerability [\#108](https://github.com/Materials-Consortia/optimade-python-tools/issues/108)

**Closed issues:**

- info endpoint duplicated? [\#120](https://github.com/Materials-Consortia/optimade-python-tools/issues/120)
- Commented-out validator [\#111](https://github.com/Materials-Consortia/optimade-python-tools/issues/111)
- FastAPI v0.44.0 supports pydantic \> 1.0.0 [\#101](https://github.com/Materials-Consortia/optimade-python-tools/issues/101)
- Server is missing /links endpoint [\#89](https://github.com/Materials-Consortia/optimade-python-tools/issues/89)
- Make sure all validators are tested [\#87](https://github.com/Materials-Consortia/optimade-python-tools/issues/87)
- The `sortable` field must be added to models [\#84](https://github.com/Materials-Consortia/optimade-python-tools/issues/84)
- Package structure [\#72](https://github.com/Materials-Consortia/optimade-python-tools/issues/72)
- Possibly make /info/{endpoint} dynamic [\#70](https://github.com/Materials-Consortia/optimade-python-tools/issues/70)
- setuptools package with server as "extra" [\#62](https://github.com/Materials-Consortia/optimade-python-tools/issues/62)
- use examples from specs as resources [\#57](https://github.com/Materials-Consortia/optimade-python-tools/issues/57)
- httptools dependency has build issues on GCC/Linux [\#54](https://github.com/Materials-Consortia/optimade-python-tools/issues/54)
- Lark grammar file for v0.9.8 [\#50](https://github.com/Materials-Consortia/optimade-python-tools/issues/50)
- type is missing in response [\#43](https://github.com/Materials-Consortia/optimade-python-tools/issues/43)
- Enforce use of autoformatter  [\#33](https://github.com/Materials-Consortia/optimade-python-tools/issues/33)
- switch license to MIT [\#28](https://github.com/Materials-Consortia/optimade-python-tools/issues/28)
- write a lark JSONTransformer / JSONdecoder [\#26](https://github.com/Materials-Consortia/optimade-python-tools/issues/26)
- server.jsonapi has no additionalProperties=false  [\#23](https://github.com/Materials-Consortia/optimade-python-tools/issues/23)
- server.jsonapi has no patternProperties  [\#22](https://github.com/Materials-Consortia/optimade-python-tools/issues/22)
- Developer-friendly pre-commit openapi.json visual diff [\#21](https://github.com/Materials-Consortia/optimade-python-tools/issues/21)
- add JSON schema API [\#12](https://github.com/Materials-Consortia/optimade-python-tools/issues/12)
- generate static documentation on github from openapi.json [\#9](https://github.com/Materials-Consortia/optimade-python-tools/issues/9)
- test how to generate a client from the openapi.json [\#8](https://github.com/Materials-Consortia/optimade-python-tools/issues/8)
- come up with suggested toolchain for validating existing optimade API against openapi.json [\#7](https://github.com/Materials-Consortia/optimade-python-tools/issues/7)
- add travis test that checks openapi.json is valid OpenAPI spec [\#6](https://github.com/Materials-Consortia/optimade-python-tools/issues/6)
- add 2 examples of how to include documentation in python classes [\#5](https://github.com/Materials-Consortia/optimade-python-tools/issues/5)
- add one-line command to update openapi.json [\#4](https://github.com/Materials-Consortia/optimade-python-tools/issues/4)

**Merged pull requests:**

- Fixed CI readme badge [\#133](https://github.com/Materials-Consortia/optimade-python-tools/pull/133) ([ml-evs](https://github.com/ml-evs))
- Add meta.description to BaseRelationshipResource [\#131](https://github.com/Materials-Consortia/optimade-python-tools/pull/131) ([CasperWA](https://github.com/CasperWA))
- Added homepage attribute to LinksResource [\#127](https://github.com/Materials-Consortia/optimade-python-tools/pull/127) ([ml-evs](https://github.com/ml-evs))
- Updated structure models and validators [\#126](https://github.com/Materials-Consortia/optimade-python-tools/pull/126) ([ml-evs](https://github.com/ml-evs))
- Minor change to fallback server.cfg [\#125](https://github.com/Materials-Consortia/optimade-python-tools/pull/125) ([ml-evs](https://github.com/ml-evs))
- Update local OpenAPI schemes prior to copying [\#124](https://github.com/Materials-Consortia/optimade-python-tools/pull/124) ([CasperWA](https://github.com/CasperWA))
- Update OpenAPI tags [\#121](https://github.com/Materials-Consortia/optimade-python-tools/pull/121) ([CasperWA](https://github.com/CasperWA))
- A few fixes related to usage as a library [\#119](https://github.com/Materials-Consortia/optimade-python-tools/pull/119) ([ml-evs](https://github.com/ml-evs))
- Add implementation to top-level meta response [\#118](https://github.com/Materials-Consortia/optimade-python-tools/pull/118) ([CasperWA](https://github.com/CasperWA))
- Add heroku deployment scripts [\#116](https://github.com/Materials-Consortia/optimade-python-tools/pull/116) ([ltalirz](https://github.com/ltalirz))
- Reorganize package [\#113](https://github.com/Materials-Consortia/optimade-python-tools/pull/113) ([CasperWA](https://github.com/CasperWA))
- Introduce grammar v0.10.1 [\#112](https://github.com/Materials-Consortia/optimade-python-tools/pull/112) ([CasperWA](https://github.com/CasperWA))
- Update to pydantic v1 [\#110](https://github.com/Materials-Consortia/optimade-python-tools/pull/110) ([CasperWA](https://github.com/CasperWA))
- Minimum requirement of django v2.2.8 [\#109](https://github.com/Materials-Consortia/optimade-python-tools/pull/109) ([CasperWA](https://github.com/CasperWA))
- Index meta-database [\#103](https://github.com/Materials-Consortia/optimade-python-tools/pull/103) ([CasperWA](https://github.com/CasperWA))
- restrict pydantic version [\#97](https://github.com/Materials-Consortia/optimade-python-tools/pull/97) ([ltalirz](https://github.com/ltalirz))
- Add /links [\#95](https://github.com/Materials-Consortia/optimade-python-tools/pull/95) ([CasperWA](https://github.com/CasperWA))
- Fix data\_returned and data\_available [\#93](https://github.com/Materials-Consortia/optimade-python-tools/pull/93) ([CasperWA](https://github.com/CasperWA))
- Use GitHub Actions for CI [\#92](https://github.com/Materials-Consortia/optimade-python-tools/pull/92) ([ml-evs](https://github.com/ml-evs))
- Remove inappropriate lint messages [\#90](https://github.com/Materials-Consortia/optimade-python-tools/pull/90) ([CasperWA](https://github.com/CasperWA))
- Fix dependencies [\#88](https://github.com/Materials-Consortia/optimade-python-tools/pull/88) ([CasperWA](https://github.com/CasperWA))
- Add sortable field to EntryInfoProperty model [\#85](https://github.com/Materials-Consortia/optimade-python-tools/pull/85) ([CasperWA](https://github.com/CasperWA))
- Validate illegal fields are not present under attributes and relationships [\#83](https://github.com/Materials-Consortia/optimade-python-tools/pull/83) ([CasperWA](https://github.com/CasperWA))
- Add references endpoint [\#78](https://github.com/Materials-Consortia/optimade-python-tools/pull/78) ([CasperWA](https://github.com/CasperWA))
- fix travis build [\#77](https://github.com/Materials-Consortia/optimade-python-tools/pull/77) ([ltalirz](https://github.com/ltalirz))
- Fix manual verification of elements\_ratios [\#76](https://github.com/Materials-Consortia/optimade-python-tools/pull/76) ([CasperWA](https://github.com/CasperWA))
- add automatic PyPI deployment [\#75](https://github.com/Materials-Consortia/optimade-python-tools/pull/75) ([ltalirz](https://github.com/ltalirz))
- Remove reference to `"all"` endpoint and rename collections submodule [\#73](https://github.com/Materials-Consortia/optimade-python-tools/pull/73) ([ml-evs](https://github.com/ml-evs))
- Updates to README and docs for v0.10.0 [\#68](https://github.com/Materials-Consortia/optimade-python-tools/pull/68) ([ml-evs](https://github.com/ml-evs))
- Adding grammar for v0.10.0 [\#66](https://github.com/Materials-Consortia/optimade-python-tools/pull/66) ([fekad](https://github.com/fekad))
- Schema updates and fixes relative to the v0.10.0 spec [\#65](https://github.com/Materials-Consortia/optimade-python-tools/pull/65) ([ml-evs](https://github.com/ml-evs))
- Break requirements down on per backend basis [\#64](https://github.com/Materials-Consortia/optimade-python-tools/pull/64) ([ml-evs](https://github.com/ml-evs))
- 0.10.0 grammer, elasticsearch transformer, setuptools extra [\#63](https://github.com/Materials-Consortia/optimade-python-tools/pull/63) ([markus1978](https://github.com/markus1978))
- Added a Lark to Django Query converter [\#61](https://github.com/Materials-Consortia/optimade-python-tools/pull/61) ([tachyontraveler](https://github.com/tachyontraveler))
- Some minor fixes [\#60](https://github.com/Materials-Consortia/optimade-python-tools/pull/60) ([ml-evs](https://github.com/ml-evs))
- Added codecov to CI [\#59](https://github.com/Materials-Consortia/optimade-python-tools/pull/59) ([ml-evs](https://github.com/ml-evs))
- Enforce black via `pre-commit` tool [\#53](https://github.com/Materials-Consortia/optimade-python-tools/pull/53) ([dwinston](https://github.com/dwinston))
- Update setup.py and version [\#51](https://github.com/Materials-Consortia/optimade-python-tools/pull/51) ([dwinston](https://github.com/dwinston))
- /structure/info endpoint [\#49](https://github.com/Materials-Consortia/optimade-python-tools/pull/49) ([fawzi](https://github.com/fawzi))
- add constrained list type [\#48](https://github.com/Materials-Consortia/optimade-python-tools/pull/48) ([dwinston](https://github.com/dwinston))
- Refactored into submodules and added test data [\#47](https://github.com/Materials-Consortia/optimade-python-tools/pull/47) ([ml-evs](https://github.com/ml-evs))
- Update structure endpoint to pre-alpha 0.10 spec [\#45](https://github.com/Materials-Consortia/optimade-python-tools/pull/45) ([ltalirz](https://github.com/ltalirz))
- Adding Resource Links [\#44](https://github.com/Materials-Consortia/optimade-python-tools/pull/44) ([tpurcell90](https://github.com/tpurcell90))
- Reblacken [\#42](https://github.com/Materials-Consortia/optimade-python-tools/pull/42) ([ml-evs](https://github.com/ml-evs))
- Documented json [\#41](https://github.com/Materials-Consortia/optimade-python-tools/pull/41) ([tpurcell90](https://github.com/tpurcell90))
- fix example output [\#40](https://github.com/Materials-Consortia/optimade-python-tools/pull/40) ([dwinston](https://github.com/dwinston))
- use jsonapi better at top level, add error response [\#36](https://github.com/Materials-Consortia/optimade-python-tools/pull/36) ([fawzi](https://github.com/fawzi))
- add JSONTransformer [\#35](https://github.com/Materials-Consortia/optimade-python-tools/pull/35) ([dwinston](https://github.com/dwinston))
- switch to MIT license [\#34](https://github.com/Materials-Consortia/optimade-python-tools/pull/34) ([ltalirz](https://github.com/ltalirz))
- Updated entry definitions and renamed Response classes [\#32](https://github.com/Materials-Consortia/optimade-python-tools/pull/32) ([ml-evs](https://github.com/ml-evs))
- update readme [\#31](https://github.com/Materials-Consortia/optimade-python-tools/pull/31) ([ltalirz](https://github.com/ltalirz))
- Seperated Links from JSON API into its own file [\#30](https://github.com/Materials-Consortia/optimade-python-tools/pull/30) ([tpurcell90](https://github.com/tpurcell90))
- simplify schema update [\#27](https://github.com/Materials-Consortia/optimade-python-tools/pull/27) ([ltalirz](https://github.com/ltalirz))
- add openapi\_diff to travis [\#25](https://github.com/Materials-Consortia/optimade-python-tools/pull/25) ([ltalirz](https://github.com/ltalirz))
- Json api add [\#24](https://github.com/Materials-Consortia/optimade-python-tools/pull/24) ([tpurcell90](https://github.com/tpurcell90))
- Added JSON diff test [\#20](https://github.com/Materials-Consortia/optimade-python-tools/pull/20) ([ml-evs](https://github.com/ml-evs))
- info endpoint [\#19](https://github.com/Materials-Consortia/optimade-python-tools/pull/19) ([fawzi](https://github.com/fawzi))
- adding run.sh script to start webserver [\#18](https://github.com/Materials-Consortia/optimade-python-tools/pull/18) ([fawzi](https://github.com/fawzi))
- error response [\#17](https://github.com/Materials-Consortia/optimade-python-tools/pull/17) ([fawzi](https://github.com/fawzi))
- Links can be strings [\#16](https://github.com/Materials-Consortia/optimade-python-tools/pull/16) ([fawzi](https://github.com/fawzi))
- response should be either many \(list\) or one \(object\), not an union [\#15](https://github.com/Materials-Consortia/optimade-python-tools/pull/15) ([fawzi](https://github.com/fawzi))
- reorg models [\#14](https://github.com/Materials-Consortia/optimade-python-tools/pull/14) ([dwinston](https://github.com/dwinston))
- Update the OptimadeMetaResponse to development schema [\#13](https://github.com/Materials-Consortia/optimade-python-tools/pull/13) ([ml-evs](https://github.com/ml-evs))
- add openapi spec validator [\#10](https://github.com/Materials-Consortia/optimade-python-tools/pull/10) ([ltalirz](https://github.com/ltalirz))
- fix test data download [\#3](https://github.com/Materials-Consortia/optimade-python-tools/pull/3) ([ltalirz](https://github.com/ltalirz))
- \[WIP\] Mongoconverter [\#1](https://github.com/Materials-Consortia/optimade-python-tools/pull/1) ([wuxiaohua1011](https://github.com/wuxiaohua1011))

## [v0.1.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.2) (2018-06-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.1...v0.1.2)

## [v0.1.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.1) (2018-06-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.0...v0.1.1)

## [v0.1.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.0) (2018-06-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/6680fb28a60ec4ff43a303b7b4dbf41e159a25b6...v0.1.0)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
