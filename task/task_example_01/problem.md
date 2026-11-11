# Problem

围绕晶体对称性选择规则对非谐散射的约束，本任务以纤锌矿 GaN、AlN 和 ZnS 为对象，考察 $6_3$ 螺旋对称性在 Normal 与 odd-axial-Umklapp 三声子过程中的模式分辨相互作用强度表现。

How does the $6_3$ screw symmetry manifest in the mode-resolved three-phonon interaction strengths of the supplied wurtzite GaN, AlN, and ZnS models, including an axial Umklapp process?

Submit `/workspace/results/answer.json` with `interaction_checks` for all three materials. The output concerns two all-incoming phonon triplets on a `3 × 3 × 6` reciprocal mesh, expressed as integer grid addresses in the supplied primitive-cell convention:

- `normal`: `[[0,0,1], [0,0,1], [0,0,-2]]`
- `odd_umklapp`: `[[0,0,2], [0,0,2], [0,0,2]]`

For screw-eigenvalue labels, use the $6_3$ operation with a $+60^\circ$ rotation about the positive crystal $c$ axis and translation $c/2$. On its invariant reciprocal-space line, define $q_z$ in primitive-cell reciprocal-lattice units and $m\in\{0,1,2,3,4,5\}$ by $\lambda_m(q_z)=\exp[2\pi i(m/6-q_z/2)]$. Resolve degenerate phonon subspaces into eigenmodes of this screw operation before assigning scalar labels. The listed triplets use the all-incoming convention, so $G_z=q_{1z}+q_{2z}+q_{3z}$ is an integer; an allowed label sector satisfies $m_1+m_2+m_3-3G_z\equiv0\pmod 6$. Thus the Normal triplet has $G_z=0$ and the odd axial Umklapp triplet has $G_z=1$.

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
