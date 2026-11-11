# pymatgen

- Installed: `pymatgen==2026.9.24`, `pymatgen-core==2026.9.23`; Python module `pymatgen`.
- Official source: https://github.com/materialsproject/pymatgen
- Official usage: https://pymatgen.org/usage.html
- Function: crystal structures, composition analysis, format conversion, and symmetry analysis.

**Python interface:** `from pymatgen.core import Structure`; `structure = Structure.from_file("POSCAR")`; `structure.to(filename="structure.cif")`. `from pymatgen.symmetry.analyzer import SpacegroupAnalyzer`; `SpacegroupAnalyzer(structure).get_space_group_symbol()` returns a symbol.

**Input/output:** POSCAR/CIF and other supported files become `Structure` objects or converted files. Symmetry tolerance is configurable through `SpacegroupAnalyzer(symprec=...)`. The separate online Materials Project client is documented in `mp-api.md`.
