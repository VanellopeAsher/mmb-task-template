# Scientific brief

## Original candidate from the expert question list
4.1 动态位点群体决定催化反应速率。

## Task interpretation
将动态活性位点问题具体化为 TiO₂ 负载 Au、Cu、AuCu、AuCu₃ 催化剂在 H₂ 还原和丁二烯选择加氢过程中的状态演化与机制可辨识性。Agent 需要比较 operando XANES 与在线质谱观测，判断哪些变化有直接证据支持，并审视 EXAFS 局部结构、产物选择性和速率因果解释的边界。

## Evidence basis
Nassereddine et al., ChemCatChem 2025, DOI: 10.1002/cctc.202500379. The paper reports Au–Cu and Au–Au coordination numbers of 3.8 ± 0.6 and 3.8 ± 0.7 for AuCu/TiO₂, respectively, consistent with well-mixed alloy nanoparticles. It reports metallic Au remaining stable during selective hydrogenation and butadiene conversion to butenes without further hydrogenation of propene or butenes.

This is a mechanism-discrimination example, not an empirically established human-hard task.

## Scoring boundary

The numerical XANES, post-edge and raw mass-channel fields check evidence provenance. The main score checks rival mechanisms against necessary predictions derived from these observations, retains mechanisms the data cannot separate, and evaluates a controlled experiment with contrasting predictions. The verifier never compares the response with a published preferred mechanism or fitted coordination number. The task still provides operational definitions and a structured response vocabulary, so an Agent trial and expert review remain necessary to measure its actual research difficulty and possible schema shortcuts.

## Limits of the supplied evidence

The source article excludes AuCu₃ EXAFS and the AuCu Cu K-edge EXAFS from quantitative interpretation because post-edge glitches compromise those spectra (Section 3.3). The published AuCu coordination numbers come from the Au L₃-edge fit and are not independently reproduced by the current Oracle. Raw mass-spectrometer channels show the reported m/z 54 decrease and m/z 56 increase in the AuCu run, but the exports have not been calibrated or fragment-deconvolved into molecular selectivities. A revised scored mechanism claim must stay within these observable limits; fitting quality, alternative structures, and uncertainty cannot be replaced by a copied paper label.

## Mechanism-discrimination redesign

The same raw MS export contains comparable annotated 130 and 150 °C windows for Au, AuCu, and AuCu₃. Median m/z 54 decreases in **all three** runs (Au 3.2907→2.5870; AuCu 12.7795→10.5035; AuCu₃ 13.7210→10.9900), while m/z 56 increases (Au 11.983→12.521; AuCu 3.746→5.681; AuCu₃ 2.5042→4.6566). These are within-run raw signals, not cross-sample calibrated rates. The common sign directly refutes the narrow claim that an *AuCu-specific* reconstruction is **required** for this signal trend; it does not rule out alloy-specific contributions to signal magnitude or reaction kinetics.

Independent 130/150 °C XANES contrasts relative to reduced states remain below 0.05 of the activation contrast for Au/Au, Cu/Cu, AuCu/Au, and AuCu/Cu. This disfavors a mechanism requiring **large bulk Au/Cu redox conversion during reaction**. It does not exclude changes in a minority surface-site population, ligand coverage, or local electronic state beneath bulk XAS sensitivity. A model-free Au-edge post-edge fingerprint check (k=3.5–9.7 Å⁻¹, k² weighting after Savitzky–Golay background subtraction) gives Au-versus-AuCu reduced correlation 0.579 and AuCu reduced-versus-130 °C correlation 0.982. Sensitivity checks over k-range and smoothing windows preserve the separation (between-sample 0.58–0.64, within-AuCu 0.98–0.99). This supports a distinct bimetallic local/electronic environment and no comparably large post-edge change during reaction, without identifying a unique coordination model or active-site morphology.

The reduced Cu transition occurs earlier in both bimetallic preparations. Hydrogen spillover, changed Cu dispersion/precursor bonding, and beam or reactor-temperature effects can each accommodate this association. The supplied experiment has no matched beam-dose, particle-size, or actual catalyst-bed-temperature intervention to identify one cause. The strongest defensible conclusion is therefore a *set*: a broadly reduced bulk state with temperature-dependent reaction signals, compatible with both stable active-site populations and minority surface redistribution. A scored mechanism task should require the Agent to reject the two narrowly falsified necessities above, retain these viable rivals, and design a matched perturbation whose predicted observations differ between a chosen pair. Numerical XANES/MS/post-edge values are evidence gates, not the final scientific target.
