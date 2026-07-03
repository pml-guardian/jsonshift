# Changelog

## [3.6.0](https://github.com/pml-guardian/jsonshift/compare/v3.5.0...v3.6.0) (2026-07-03)


### Features

* add $pow operator and numeric formatting support to $format ([adb5465](https://github.com/pml-guardian/jsonshift/commit/adb54650cb3b5482c2144abb3a3b1c82f0c43d08))
* add $pow operator, decimal math support and number formatting ([74763da](https://github.com/pml-guardian/jsonshift/commit/74763dadaf5767231643c2668d5f39781bf45486))
* add ci and release-please workflows ([47bf023](https://github.com/pml-guardian/jsonshift/commit/47bf023d8e46c1765941562ee406a2ade0731075))
* add ci and release-please workflows ([e5c2648](https://github.com/pml-guardian/jsonshift/commit/e5c2648916b7bb704f51fdd9ebd78e08aebbde95))
* add math, date arithmetic, formatting and masking to dynamic defaults ([461100b](https://github.com/pml-guardian/jsonshift/commit/461100b6795c45e13aaa665d9284ecf6ee2539ec))
* **array-mapper:** add advanced list mapping with wildcards, fixed indices and optional fields ([f8662d8](https://github.com/pml-guardian/jsonshift/commit/f8662d80185f1f038328e1cd6b18df25b62289e9))
* **array-mapper:** add recursive nested wildcard support ([4784674](https://github.com/pml-guardian/jsonshift/commit/478467470aff0bbf9287ca277a6cae4382b79d0a))
* **array-mapper:** add recursive nested wildcard support ([0afc25e](https://github.com/pml-guardian/jsonshift/commit/0afc25e5c6fec84a9bcbb0ee28c0e1da4b45d769))
* **format:** add $format.date with optional parse support ([e9f56e2](https://github.com/pml-guardian/jsonshift/commit/e9f56e2b4151224218cbf58d15f2b03557320b20))
* **mapper:** add $any operator for list membership checks ([ba411c8](https://github.com/pml-guardian/jsonshift/commit/ba411c80290a62727aa38cc518e598625261a2c9))
* **mapper:** add $if operator and comparison operators ($eq, $ne, $gt, $gte, $lt, $lte) ([c6a44e2](https://github.com/pml-guardian/jsonshift/commit/c6a44e291778cd0786bb8f09afd1cee27ab07478))
* **mapper:** add $len operator and [+] append index ([8a4f31b](https://github.com/pml-guardian/jsonshift/commit/8a4f31b20d3e16e96a1763f710caa1ada54144dd))
* **mapper:** add dynamic string functions to defaults DSL ([532d541](https://github.com/pml-guardian/jsonshift/commit/532d541378f40aabf088d048004af9462ebc0a20))
* **mapper:** add title and capitalize string functions and None propagation ([31b6f88](https://github.com/pml-guardian/jsonshift/commit/31b6f88f1d3c3e372bdd8460f9ea746d699040c3))
* **mapper:** extend $now with date parts and arithmetic ([f561c7d](https://github.com/pml-guardian/jsonshift/commit/f561c7d5e61b606d01c05f8f6f51c2952e45c6f1))
* **mapper:** support infinite recursive wildcards with full flattening ([38bbdd9](https://github.com/pml-guardian/jsonshift/commit/38bbdd99671c30dbd5ad27f40dfb17fe70b255b8))


### Bug Fixes

* **cli:** serialize date, datetime and time to ISO-8601 ([612fc34](https://github.com/pml-guardian/jsonshift/commit/612fc34cbb10d6cef3c2c35903b40a8435b34045))
* **mapper:** align $path optional behavior with map and propagate _MISSING in dynamic operators ([2c94d0f](https://github.com/pml-guardian/jsonshift/commit/2c94d0f7b616ad9bf5049e3c0646b2a2347e24cb))
* **mapper:** broadcast static wildcard defaults across all list elements ([d297776](https://github.com/pml-guardian/jsonshift/commit/d297776da2e88993acf42aa69eb21219fc09d1cb))
* resolve dynamic by in math operators to support nested expressions ([6b911e0](https://github.com/pml-guardian/jsonshift/commit/6b911e0b2b08188948e1f226a1d6882479b88784))
