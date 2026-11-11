# Feasibility report

This author-only report identifies independently checkable signals for the phonon-scattering question. It does not assert that a full general relationship between nonsymmorphic symmetry and bulk thermal conductivity has been established.

## Evidence and provenance

Eight original NIMS PhononDB archives contain crystal structures, displaced-structure/force data, polynomial potential parameters, and lattice thermal-conductivity logs. Their source pages and SHA-256 checksums are in `authoring/provenance/nims_manifest.json`. They cover wurtzite/zincblende GaN, AlN, ZnS, and diamond/hexagonal Si. The archives and installed Phonopy/Phono3py toolchain allow several analyses without an external private code.

## Checkable feasibility claims

The source logs contain temperature-dependent conductivity tensors for all eight models. Wurtzite/zincblende comparisons do not have one universal sign across the three compounds. The wurtzite archives also contain data from which third-order interaction strengths can be evaluated; author-side probes of GaN, AlN, and ZnS show near-zero channels in sampled high-symmetry-line mode classes. A restricted screw-eigenvalue condition can be checked against those classes. `reproduce.sh` checks the availability of the original observation types; `authoring/evidence/` records cross-checks and numerical limitations. `witness/` contains an optional bounded analysis.

## Resource and access limits

The data and software are provided through `environment/`, with compute limits in `task.toml`. The witness uses only those scientific inputs plus author-only code; it is not made available to the evaluated Agent. Other scientifically valid approaches may use different tools or intermediate evidence.

## Remaining uncertainty

Symmetry-constrained zeros on selected modes leave the magnitude and direction of any bulk conductivity effect unresolved. Degeneracies, phase space, surviving couplings, force-field error, and polymorph differences remain relevant. Agent difficulty requires independent model trials under the specified environment and time limit.
