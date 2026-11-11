# Scoring shortcut audit

The evaluated artifact contains 15 numerical observables derived from three original wurtzite force archives. Six sector shares and six effective sector counts depend on the distribution of squared three-phonon couplings across screw-character sectors. Three ratios compare the total allowed coupling strength of the selected odd-Umklapp and Normal triplets. The verifier does not award points for a formula, a symmetry label count, conductivity values copied from `LTC-calc.log`, or explanatory text.

| Candidate shortcut | Observable it can recover | Scored values it cannot recover |
| --- | --- | --- |
| Multiply three screw eigenvalues | Necessary allowed-sector condition | Model-specific sector weights and interaction-strength ratios |
| Count modes in each screw sector | Numbers of possible mode combinations | Squared coupling strength carried by each combination |
| Read source thermal-conductivity logs | Published transport tensors and their ratios | Mode-resolved three-phonon coupling distribution |
| Guess that forbidden couplings vanish | A qualitative suppression prediction | Largest allowed-sector share, effective sector count, odd/Normal strength ratio |

The reference cross-check reconstructs force constants, resolves the screw operation and mode labels, computes interactions, and compares 15 values against the answer key. `check_verifier.py` rejects a submission containing only the old formula and transport fields and rejects perturbations of the interaction values. The scorer accepts numerically equivalent results from any method that reaches the published observables.

The sample's public answer key is for authoring review. A live item packages `solution/`, `tests/`, and `authoring/` outside the Agent's access boundary. Empirical Agent difficulty is established by timed trials on hidden items.
