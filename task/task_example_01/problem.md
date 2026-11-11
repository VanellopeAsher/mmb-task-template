# Problem

How does the $6_3$ screw symmetry manifest in the mode-resolved three-phonon interaction strengths of the supplied wurtzite GaN, AlN, and ZnS models, including an axial Umklapp process?

Submit `/workspace/results/answer.json` with `interaction_checks` for all three materials. The output concerns two all-incoming phonon triplets on a `3 × 3 × 6` reciprocal mesh, expressed as integer grid addresses in the supplied primitive-cell convention:

- `normal`: `[[0,0,1], [0,0,1], [0,0,-2]]`
- `odd_umklapp`: `[[0,0,2], [0,0,2], [0,0,2]]`

For each triplet, group the squared three-phonon interaction strengths by the three screw-eigenvalue labels of the participating modes. For each symmetry-allowed label sector, sum its strengths, then divide by the sum across all allowed sectors. Report `largest_sector_share`, the largest resulting share, and `effective_sector_count`, the reciprocal of the sum of squared shares. Also report `odd_normal_total_ratio`, the total squared interaction strength in allowed sectors for `odd_umklapp` divided by that for `normal`. These quantities are dimensionless and refer to the supplied force models. The verifier accepts absolute errors of `0.0002` for each share and ratio, and `0.05` for each effective sector count.

```json
{
  "interaction_checks": {
    "GaN": {
      "normal": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_umklapp": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_normal_total_ratio": 0.0
    },
    "AlN": {
      "normal": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_umklapp": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_normal_total_ratio": 0.0
    },
    "ZnS": {
      "normal": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_umklapp": {"largest_sector_share": 0.0, "effective_sector_count": 0.0},
      "odd_normal_total_ratio": 0.0
    }
  },
  "analysis": "Optional research notes; this field does not affect reward"
}
```

`analysis` may be omitted or left empty. Only the numerical `interaction_checks` fields determine the reward.
