# hiPhive

- Installed: `hiphive==1.5`; Python module `hiphive`.
- Official source: https://gitlab.com/materials-modeling/hiphive
- Official API guide: https://hiphive.materialsmodeling.org/get_started/construct_fcp.html
- Function: high-order force-constant models from displaced structures and forces.

**Python interface:** `from hiphive import ClusterSpace, StructureContainer, ForceConstantPotential`; `cs = ClusterSpace(primitive_atoms, cutoffs=[5.0, 4.0])`; `container = StructureContainer(cs)`. `primitive_atoms` is an ASE `Atoms` structure and cutoffs are in ångström. The official guide documents adding displaced structures and fitting parameters.

**Input/output:** Displaced atomistic structures with forces are fitted to a `ForceConstantPotential`, which can export force constants. hiPhive does not calculate electronic forces itself.
