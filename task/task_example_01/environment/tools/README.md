# Available scientific tools

- `inspect_nims.py` lists the source archives, reports their members and crystal structures, reads full temperature-dependent thermal-conductivity tensors, or extracts any member for independent analysis. Use `python /workspace/tools/inspect_nims.py --help`.
- `screw_selection.py` evaluates a necessary character-product condition for nondegenerate modes on a screw-invariant line. It is a theoretical check, not a material-specific scattering-rate calculation.
- `probe_interactions.py` reconstructs GaN third-order force constants from the original displacement and force data, then compares numerically tiny three-phonon interaction strengths for screw-axis and off-axis grid triplets. This is an optional diagnostic; it does not identify mode representations or prove the source of a vanishing coupling. Run `python /workspace/tools/probe_interactions.py --help`.
- `spglib` identifies symmetry operations and space-group settings from atomic positions. Check numerical tolerance and the distinction between a screw/glide operation and a genuinely nonsymmorphic space group.
- `phonopy` provides harmonic phonons, bands, eigenvectors, and mode analysis from the supplied second-order force data.
- `phono3py` provides third-order force-constant reconstruction, phonon interactions, scattering rates, and lattice thermal conductivity from the supplied displacement and force sets. Different meshes, isotope settings, and transport approximations can be explored.
- `symfc`, `seekpath`, NumPy, SciPy, pandas, SymPy, and matplotlib support independent symmetry, numerical, statistical, and visualization analyses.

The supplied archives also contain polynomial machine-learning potential parameters and original VASP-related input records. VASP itself is proprietary and is not installed; the provided force and displacement data allow open-source downstream analysis without rerunning VASP. These tools are options, not an ordered recipe. Record exact commands, versions, and settings for any experiment used in a conclusion.
