# Phono3py

- Installed: `phono3py==4.10.0`; CLI `phono3py`; Python module `phono3py`.
- Official source: https://github.com/phonopy/phono3py
- Official CLI/API: https://phonopy.github.io/phono3py/command-options.html and https://phonopy.github.io/phono3py/api-reference.html
- Function: third-order force constants, three-phonon scattering, and lattice thermal-conductivity calculations.

**CLI interface:** `phono3py --help` lists options for cells, displacements, force constants, meshes, and transport quantities. `phono3py --config settings.conf` reads setting tags. Inputs include Phono3py YAML, force/displacement datasets, and FC2/FC3 files; generated artifacts can include YAML, HDF5, and logs.

**Python interface:** `import phono3py; ph3 = phono3py.load("phono3py.yaml")`; inspect `help(phono3py.load)` and the linked API for accepted data arguments. Supplied NIMS ZIPs contain compressed Phono3py YAML and force members, which can be extracted with `inspect_nims.py`.
