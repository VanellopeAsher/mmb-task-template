# spglib

- Installed: `spglib==2.8.0`; Python module `spglib`.
- Official source: https://github.com/spglib/spglib
- Official Python API: https://spglib.readthedocs.io/en/stable/python-interface.html
- Function: space groups, crystal symmetry operations, and standardized cells.

**Input/API:** A cell is `(lattice, fractional_positions, atomic_numbers)`, with lattice vectors as rows. `spglib.get_symmetry_dataset(cell, symprec=1e-5)` returns the space-group dataset, including `.number`, `.international`, and `.rotations`. `spglib.standardize_cell(cell, to_primitive=True, symprec=1e-5)` returns transformed cell arrays.

**Output/limit:** Results are Python objects/arrays. `symprec` is a positional tolerance; changing it can change the detected symmetry.
