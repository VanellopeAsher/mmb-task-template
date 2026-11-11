# Scientific input data

`nims/` contains eight original ZIP archives from Atsushi Togo's NIMS Materials Data Repository lattice-thermal-conductivity collection and a `catalog.json` with source links and checksums. The three same-composition polymorph pairs are GaN, AlN, and ZnS (wurtzite P6_3mc, 186; zincblende F-43m, 216). The two Si datasets are diamond Fd-3m, 227, and hexagonal P6_3/mmc, 194. These space-group labels are source metadata.

Each ZIP contains `phono3py_mlp_eval_fc3_disp.yaml.xz` (structure and cubic-force-constant displacements), `FORCES_FC3.xz` (corresponding forces), `phonopy_mlp_eval_fc2_dataset.yaml.xz` (harmonic displacements and forces), `phonopy_training_dataset.yaml.xz`, `polymlp.yaml.xz`, `vasp-settings.tar.xz`, `LTC-calc.log` (temperature-dependent conductivity calculation), and `band_pdos.png`. The ZIPs are not pre-extracted; `tools/inspect_nims.py` can inspect or extract any member.

Source index: https://github.com/atztogo/phonondb/blob/main/mdr/phonondb_LTC/README.md. Each source page, file size, and SHA-256 digest is recorded in `catalog.json`. The NIMS pages state CC BY 4.0; attribution is required. The archives contain computational data based on PBEsol and fitted potentials.
