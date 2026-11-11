# pypolymlp

- Installed: `pypolymlp==0.22.1`; Python module `pypolymlp`; CLI program `pypolymlp-calc`.
- Official source: https://github.com/sekocha/pypolymlp
- Official usage: https://sekocha.github.io/pypolymlp/ and https://github.com/sekocha/pypolymlp/blob/develop/docs/calc_eos.md
- Function: polynomial machine-learning interatomic potentials, force/property calculations, and model analysis.

**CLI interface:** `pypolymlp-calc --help` lists calculations. `pypolymlp-calc --eos --poscar POSCAR --pot polymlp.yaml` is an upstream-documented example accepting a structure and an existing potential. The package also has Python calculation interfaces documented upstream.

**Input/output:** Potential formats include `polymlp.yaml` and legacy `polymlp.lammps`; output files depend on the chosen calculation. NIMS ZIPs contain `polymlp.yaml.xz`, which can be extracted/decompressed. Potential elements and provenance must match the queried structure.
