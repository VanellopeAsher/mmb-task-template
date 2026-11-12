# Input data

CIF structures are sourced from the public `defective-UiO-66` repository associated with Islamov et al., *Correlated missing linker defects increase thermal conductivity in metal-organic framework UiO-66*, Chemical Science 2023, DOI: 10.1039/D2SC06120A.

The source repository provides randomly distributed missing-linker and missing-cluster structures at multiple nominal concentrations, plus correlated defect structures with reo, scu, and bcu topologies. The bootstrap downloads selected CIFs and verifies their Git blob SHA-1 before renaming them to opaque sample IDs. The three source primitive-cell structures are repeated 3×3×3 with ASE, so all nine Agent-visible CIFs have the same cell scale. Repetition preserves each source structure's local ordering and defect fraction.

Important: the source GitHub repository does not declare an explicit software/data licence. The package therefore does not redistribute CIFs; it fetches from the source at build time. Confirm permission or replace the source with a licensed equivalent before public benchmark redistribution.
