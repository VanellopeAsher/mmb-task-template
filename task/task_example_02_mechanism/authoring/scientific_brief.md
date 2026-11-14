# Scientific brief

## Original candidate from the expert question list
4.1 动态位点群体决定催化反应速率。

## Task interpretation
将动态活性位点问题具体化为 TiO₂ 负载 Au、Cu、AuCu、AuCu₃ 催化剂在 H₂ 活化后的丁二烯加氢阶段的状态与机制可辨识性。Agent 需要比较 operando XANES 与在线质谱观测，判断哪些变化有直接证据支持，并审视 EXAFS 局部结构、产物选择性和速率因果解释的边界。

## Evidence basis
Nassereddine et al., ChemCatChem 2025, DOI: 10.1002/cctc.202500379. The paper reports Au–Cu and Au–Au coordination numbers of 3.8 ± 0.6 and 3.8 ± 0.7 for AuCu/TiO₂, respectively, consistent with well-mixed alloy nanoparticles. It reports metallic Au remaining stable during selective hydrogenation and butadiene conversion to butenes without further hydrogenation of propene or butenes.

This is a mechanism-discrimination example, not an empirically established human-hard task.

## Scoring boundary

The task scores the hydrogenation stage. The verifier requires correct source-derived XANES, post-edge and raw MS values, both process conclusions, all four mechanism evidence states, and the three inference limits. The submitted Au and AuCu MS contrasts must also have the observed directions. Reward is binary.

The observations support persistence of a predominantly reduced alloy environment and a same-direction response in the single-metal Au control. Large-scale bulk redox and demixing lack support as dominant explanations. Minority surface Cu redistribution and fixed-site coverage or kinetics remain unresolved. The evidence does not establish a fixed active-site population, calibrated yield or selectivity, or a shared elementary mechanism.

Early Cu reduction causality is outside scoring. Optional `follow_up` text is unscored. See [the scientific reference](evidence/reaction_mechanism_reference.md) and [the rubric](rubric.yaml).

## Limits of the supplied evidence

The source article excludes AuCu₃ EXAFS and the AuCu Cu K-edge EXAFS from quantitative interpretation because post-edge glitches compromise those spectra (Section 3.3). The published AuCu coordination numbers come from the Au L₃-edge fit and are not independently reproduced by the current Oracle. Raw mass-spectrometer channels show the reported m/z 54 decrease and m/z 56 increase in the AuCu run, but the exports have not been calibrated or fragment-deconvolved into molecular selectivities. The current score checks the observed raw channels and explicit limits on inference.

## Reaction-stage evidence

The same raw MS export contains comparable annotated 130 and 150 °C windows for Au, AuCu, and AuCu₃. Median m/z 54 decreases in **all three** runs (Au 3.2907→2.5870; AuCu 12.7795→10.5035; AuCu₃ 13.7210→10.9900), while m/z 56 increases (Au 11.983→12.521; AuCu 3.746→5.681; AuCu₃ 2.5042→4.6566). These are within-run raw signals, not cross-sample calibrated rates. The common sign is also present in the single-metal control and does not establish a shared elementary mechanism.

Independent 130/150 °C XANES contrasts relative to reduced states remain below 0.05 of the activation contrast for Au/Au, Cu/Cu, AuCu/Au, and AuCu/Cu. This disfavors a mechanism requiring **large bulk Au/Cu redox conversion during reaction**. It does not exclude changes in a minority surface-site population, ligand coverage, or local electronic state beneath bulk XAS sensitivity. A model-free Au-edge post-edge fingerprint check (k=3.5–9.7 Å⁻¹, k² weighting after Savitzky–Golay background subtraction) gives Au-versus-AuCu reduced correlation 0.579 and AuCu reduced-versus-130 °C correlation 0.982. Sensitivity checks over k-range and smoothing windows preserve the separation (between-sample 0.58–0.64, within-AuCu 0.98–0.99). This supports a distinct bimetallic local/electronic environment and no comparably large post-edge change during reaction, without identifying a unique coordination model or active-site morphology.

## Historical activation and follow-up work

The earlier activation analysis and prospective experiment designs remain in [early Cu identifiability](evidence/early_cu_identifiability.md) and [experiment reference](evidence/experiment_reference.md). They describe earlier research and are outside the current reward.
