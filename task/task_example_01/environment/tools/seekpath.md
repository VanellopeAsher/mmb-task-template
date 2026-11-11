# SeeK-path

- Installed: `seekpath==2.2.2`; Python module `seekpath`.
- Official source: https://github.com/materialscloud-org/seekpath
- Official API: https://seekpath.readthedocs.io/en/latest/
- Function: standardized high-symmetry points and band paths in reciprocal space.

**Python interface:** `seekpath.get_path((lattice, fractional_positions, atomic_numbers))` accepts a crystal-cell tuple and returns a dictionary with `point_coords`, `path`, and standardized cell information. `seekpath.get_explicit_k_path(...)` returns sampled path coordinates.

**Output/limit:** Point labels are tied to the returned cell convention. Coordinates and labels must be transformed consistently if compared with a different primitive/conventional cell.
