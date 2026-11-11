# Atomic Simulation Environment (ASE)

- Installed: `ase==3.29.0`; CLI `ase`; Python module `ase`.
- Official source: https://gitlab.com/ase/ase
- Official CLI/API: https://docs.ase-lib.org/cmdline.html and https://docs.ase-lib.org/ase/io/io.html
- Function: atomistic structures, file I/O, calculator interfaces, and simulation analysis.

**CLI interface:** `ase --help` lists commands; `ase info structure.cif` inspects a file; `ase convert structure.cif POSCAR` converts supported formats. `ase convert --help` shows format options for the installed build.

**Python interface:** `from ase.io import read, write`; `atoms = read("structure.cif")`; `write("POSCAR", atoms)`. I/O accepts many structure formats and returns/writes ASE `Atoms`. A calculator interface may require a separately installed engine or potential.
