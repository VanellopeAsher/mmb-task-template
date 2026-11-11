# Feasibility report

This author-only report identifies independently checkable signals for the phonon-scattering question. It does not assert that a full general relationship between nonsymmorphic symmetry and bulk thermal conductivity has been established.

## Evidence and provenance

Eight original NIMS PhononDB archives contain crystal structures, displaced-structure/force data, polynomial potential parameters, and lattice thermal-conductivity logs. Their source pages and SHA-256 checksums are in `authoring/provenance/nims_manifest.json`. They cover wurtzite/zincblende GaN, AlN, ZnS, and diamond/hexagonal Si. The archives and installed Phonopy/Phono3py toolchain allow several analyses without an external private code.

## Checkable feasibility claims

The source logs contain temperature-dependent conductivity tensors for all eight models, with opposite wurtzite/zincblende orderings among the three compounds. `reproduce.sh` checks those observations and runs `signal_check.py` in the pinned scientific image. For GaN, AlN, and ZnS it verifies a `6_3` operation in the supplied structure, reconstructs nonzero three-phonon interactions from the original force/displacement data, and verifies that one axial triplet has more near-zero interaction elements than one off-axis triplet on the same mesh. These are existence and discriminability checks. The optional `witness/` contains a bounded analysis; `authoring/evidence/` records further cross-checks and numerical limitations.

## Why a bounded answer exists

On a screw-invariant line, the crystal operation acts on phonon-mode subspaces. An invariant cubic coupling must belong to the identity component of the product representation; non-identity components are therefore symmetry-forbidden. This follows the group-theoretic anharmonic-scattering framework of [Yang et al. (2021)](https://doi.org/10.1103/PhysRevB.103.184302). The fact supplies a finite, testable class of constraints without fixing a particular investigator's derivation. The verified source files provide the symmetry operation, force data from which the couplings can be calculated, and transport observations for several compounds. The successful pinned-image check establishes that these ingredients yield both suppressed and surviving coupling signals, while the polymorph ordering distinguishes a bounded relationship from a universal conductivity claim. A supported answer with explicit domain and limits is therefore reachable from the supplied materials.

## Resource and access limits

The data and software are provided through `environment/`, with compute limits in `task.toml`. The witness uses only those scientific inputs plus author-only code; it is not made available to the evaluated Agent. Other scientifically valid approaches may use different tools or intermediate evidence.

## Remaining uncertainty

The axial/off-axis contrast alone does not assign its cause or quantify its effect on bulk conductivity. Degeneracies, phase space, surviving couplings, force-field error, and polymorph differences remain relevant. The feasibility gate establishes accessible signal and distinguishable transport observations; the answer and scientific assessment remain separate.
