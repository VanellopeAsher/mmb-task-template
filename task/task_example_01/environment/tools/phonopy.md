# Phonopy

- Installed: `phonopy==4.10.0`; CLI `phonopy`; Python module `phonopy`.
- Official source: https://github.com/phonopy/phonopy
- Official CLI/API: https://phonopy.github.io/phonopy/command-options.html and https://phonopy.github.io/phonopy/phonopy-module.html
- Function: harmonic force constants, phonon modes, dispersions, density of states, and symmetry-aware supercells.

**CLI interface:** `phonopy --help` shows all options. `phonopy -c POSCAR --dim 2 2 2 -d` accepts a structure and writes displaced supercells. `phonopy --config settings.conf` reads a settings file. Calculator flags such as `--qe` and `--lammps` select I/O conventions; they do not install those calculators.

**Python interface:** `from phonopy import load; phonon = load("phonopy.yaml")`. Input is a Phonopy YAML/structure and optional force data; output is a `Phonopy` object or CLI-generated YAML, force constants, mesh, or plots. Electronic forces require a separate calculator or supplied data.
