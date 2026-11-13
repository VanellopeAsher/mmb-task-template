# BAs force-model input

`ba/` contains the original `Example-BAs/input` files from [FourPhonon](https://github.com/FourPhonon/FourPhonon) at commit `5b814b337e03e72907a15a2c953723171fba7102` (GPL-3.0). The files define one zincblende BAs harmonic, cubic, and quartic force model. They are model inputs, not experimental measurements.

| File | SHA-256 |
| --- | --- |
| `CONTROL` | `0a4b417db4aa7a8dcfab5c03f1937ad14171cfb0a006cc56595cb12886cd8364` |
| `FORCE_CONSTANTS_2ND` | `e16bb49f78686a3fbff7ff613e7bc90ee6ca79796049eb75521f93b412c78529` |
| `FORCE_CONSTANTS_3RD` | `8af8615fd9ac954ce3e028c9595a5313b78aabc944c51d38081089391b18171c` |
| `FORCE_CONSTANTS_4TH` | `25046429a7e5b3b8c3c4b1c30c134d660a9a9c8ae7fddc432cac91a846e58905` |

The upstream `CONTROL` requests 300 K, 16³, and `scalebroad=0.1`. It is preserved for provenance. The present task uses 350 K and `scalebroad=1.0` on 16³ and 20³ meshes as stated in `problem.md`. The upstream repository publishes 300 K outputs; those are not the answer to this task. The installed solver is a pinned FourPhonon CPU build with a GNU Fortran port and a correction to six out-of-bounds sampling loops; its patch is in `environment/fourphonon.patch`.
