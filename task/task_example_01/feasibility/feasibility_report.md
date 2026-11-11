# Feasibility report

This author-only report identifies independently checkable signals for the phonon-scattering question. It does not assert that a full general relationship between nonsymmorphic symmetry and bulk thermal conductivity has been established.

## Evidence and provenance

Eight original NIMS PhononDB archives contain crystal structures, displaced-structure/force data, polynomial potential parameters, and lattice thermal-conductivity logs. Their source pages and SHA-256 checksums are in `authoring/provenance/nims_manifest.json`. They cover wurtzite/zincblende GaN, AlN, ZnS, and diamond/hexagonal Si. The archives and installed Phonopy/Phono3py toolchain allow several analyses without an external private code.

## Checkable feasibility claims

The source logs contain temperature-dependent conductivity tensors for all eight models, with opposite wurtzite/zincblende orderings among the three compounds. `reproduce.sh` checks those observations and runs `signal_check.py` in the pinned scientific image. For GaN, AlN, and ZnS it verifies a `6_3` operation in the supplied structure, reconstructs nonzero three-phonon interactions from the original force/displacement data, and verifies that one axial triplet has more near-zero interaction elements than one off-axis triplet on the same mesh. These are existence and discriminability checks. The optional `witness/` contains a bounded analysis; `authoring/evidence/` records further cross-checks and numerical limitations.

## Resource and access limits

The data and software are provided through `environment/`, with compute limits in `task.toml`. The witness uses only those scientific inputs plus author-only code; it is not made available to the evaluated Agent. Other scientifically valid approaches may use different tools or intermediate evidence.

## Remaining uncertainty

The axial/off-axis contrast alone does not assign its cause or quantify its effect on bulk conductivity. Degeneracies, phase space, surviving couplings, force-field error, and polymorph differences remain relevant. The feasibility gate establishes accessible signal and distinguishable transport observations; the answer and scientific assessment remain separate.
