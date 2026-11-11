# Research task design: when do phonon selection rules predict dominant scattering?

## Decision on the present example

The present problem fixes the compounds, mesh, two triplets, and every scored statistic. One Phono3py calculation supplies the complete answer. It asks for coupling strengths on a symmetry-invariant line, not the dominant scattering of heat-carrying modes throughout the Brillouin zone. It contains neither four-phonon rates nor a transport comparison. It therefore fails the intended research-task standard by inspection; a timed Agent run is unnecessary to reach that conclusion.

## Scientific question to preserve

The replacement must address the original question: **under which material and thermodynamic conditions do phonon scattering selection rules correctly predict the dominant scattering mechanism, and where do they fail?** A rule can constrain the allowed phase space or a matrix element. The actual rate also depends on energy and momentum conservation, anharmonic interaction strength, and mode occupation. A small three-phonon phase space can coexist with strong four-phonon scattering. The research target is the boundary between a useful rule-based prediction and a misleading one, as reflected in mode lifetimes and thermal conductivity.

## Structural difficulty gate

A candidate problem qualifies only if its answer requires all of these scientific decisions:

1. Decide which modes, temperatures, and material conditions carry enough heat to matter. A conspicuous selection rule on a special symmetry line alone cannot settle bulk transport.
2. Form competing predictions from allowed-channel structure and energy-conserving phase space, then test them against explicit interaction strengths and three- and four-phonon rates.
3. Determine whether a mismatch arises from the rule's domain, the magnitude of allowed matrix elements, occupation or temperature effects, or a higher-order channel. These explanations must produce different observable consequences in the supplied environment.
4. Check whether the inferred dominant mechanism changes mode lifetimes and thermal conductivity in the predicted direction, with convergence and uncertainty sufficient to distinguish the alternatives.

If the stated inputs and output fields reduce the task to one obvious calculation, or a single table/log/lookup supplies the result, reject the candidate before packaging it. Adding more fields from the same calculation does not change this verdict. The existence of one oracle sequence is expected; the issue is whether discovering a valid sequence requires consequential scientific choices among plausible alternatives. A multi-step computation still fails if the problem dictates those choices. The problem must leave conditions, calculations, and competing explanations for the solver to resolve while making the final result objectively checkable.

## Candidate answer contract and independent check

### Physical setting

A promising concrete setting is a *newly computed*, matched pressure–temperature series for BP and BAs. The published comparison motivates this choice: three-phonon acoustic-channel restrictions and four-phonon scattering affect the pressure response differently in these two compounds. The author would release relaxed structures and raw force/displacement observations at several pressures, plus a callable force model for additional conditions. The author would keep the computed scattering and transport outcome tables outside the Agent environment. Chemical identity need not be hidden; the target pressures, temperatures, force model, and requested numerical boundary must differ from published figures so that a literature lookup cannot supply the answer.

The scientific task would ask for the **domain in pressure and temperature where a specified dispersion/selection-rule forecast correctly ranks two matched conditions by the scattering of heat-carrying phonons, and the boundary where that ranking reverses**. The forecast must be frozen from harmonic information before inspecting anharmonic outcomes; otherwise the task could redefine the rule after seeing the answer. The solver must determine which heat-carrying modes matter, inspect allowed channels and phase space, obtain actual three- and four-phonon rates, and compare the resulting lifetimes and thermal conductivity. A BP/BAs contrast can expose two plausible but wrong explanations for a similar shape of κ(P): the change in acoustic three-phonon channels and the opposing higher-order response. The problem statement should give the physical question and answer contract, not the diagnostic sequence.

### Answer contract

An Agent-facing question, once the physical cases are selected, can be as compact as: “Across the supplied matched material conditions, where does a symmetry- and kinematics-based screen correctly predict the relative scattering of heat-carrying phonons, and where does that prediction cease to explain the mode-lifetime and lattice-thermal-conductivity ordering?” The rest of `problem.md` would define the output artifact and observables only. It would not list the decoy types, name a decisive mode, or prescribe which calculation comes first.

For each material and one declared temperature interval, `answer.json` would report:

- The condition pairs for which the *predeclared harmonic forecast* gets the ordering of transport-weighted three-phonon rates right, and the pairs where it gets that ordering wrong. A pairwise ordering avoids claiming that a phase-space count gives an absolute rate.
- The pressure/temperature boundary at which the forecast's ordering of *total* scattering rates or full κ changes from correct to wrong. Rate ranking and κ ranking are separate because group velocities and heat-capacity weights can change.
- For the decisive pair near that boundary: the ratio of allowed three-phonon phase spaces, the ratio of transport-weighted three-phonon rates, the four-phonon fraction of total rate, and the ratios of three-phonon-only and full κ. These numerics distinguish a matrix-element reversal from a higher-order reversal and from a transport-weighting reversal.

These fields must be tied to the *same* physical force model and temperature convention. Numerical tolerances should come from pre-established mesh, force-constant, and sampling convergence, not from a convenient scoring margin. The actual values cannot be filled into this design document without the underlying calculations.

A compact JSON contract for a final item would have `pair_results[<pair_id>]` with numerical `screen_index_ratio`, `three_phonon_rate_ratio`, `three_plus_four_rate_ratio`, `kappa_three_ratio`, `kappa_full_ratio`, and two `four_phonon_fraction` values; `valid_pair_ids` and `failure_pair_ids` would identify the tested domain. `decisive_counterexample` would identify a pair and report three independently checkable reversal flags: `kinematic_to_cubic`, `cubic_to_total_rate`, and `total_rate_to_conductivity`. More than one flag can be true; the task must not force a single cause when mechanisms coexist. The author must freeze each pair, direction, temperature, rate normalization, and numerical tolerance in the final contract. Every flag is checked against the submitted ratios and the hidden reference values; guessing labels cannot earn a passing score.

The forecast can be made unambiguous without prescribing a software route. At each condition, use harmonic heat-carrying capacity `b(λ) = C(λ)[v(λ)·e]^2` and a symmetry-filtered three-phonon *kinematic kernel* `P3(λ,T)` on the same reciprocal mesh. `P3` retains energy and momentum conservation, Bose occupation, frequency normalization, and the symmetry-allowed channel mask from the golden-rule rate expression, while replacing the unknown squared cubic matrix element with the same constant for all allowed events. Define the screening index `H3 = Σλ b(λ)P3(λ,T)/Σλ b(λ)`. For a matched pair with a predeclared minimum separation in `H3`, the screen forecasts a lower three-phonon rate for the condition with lower `H3`. The oracle compares this ranking with `G3 = Σλ b(λ)γ3(λ)/Σλ b(λ)`, then with the full rate and κ rankings. The `H3 → G3` discrepancy can then be assigned to actual cubic matrix elements rather than omitted occupation factors. This is a test of the screening *inference*, not an assertion that `H3` is a physical scattering rate. Pair construction must avoid near ties in `H3`; otherwise numerical noise would decide the label.

One objective definition of “dominant for heat transport” is available within a common single-mode relaxation-time approximation. For each mode λ and transport direction e, compute `γ3(λ)`, `γ4(λ)`, and the modal conductivity weight `w(λ) ∝ C(λ)[v(λ)·e]^2/[γ3(λ)+γ4(λ)]`, normalized over modes. Then `F4 = Σλ w(λ) γ4(λ)/[γ3(λ)+γ4(λ)]`. A crossing of `F4 = 0.5` is a reproducible *rate-dominance* boundary. It does **not** automatically mean the selection rule failed: a rule that predicts suppressed three-phonon channels may correctly flag the conditions where four-phonon scattering becomes important. Separately score the actual conductivity impact `D4 = 1 - κ3+4/κ3`. A claim of rule sufficiency requires agreement between the predeclared harmonic pairwise forecast and the relevant rate or κ ordering, not merely an `F4` threshold. These definitions must be frozen before reference calculations and published in the answer contract; they do not tell the solver which numerical route to use.

The independent verifier compares the crossing, conductivity, and modal-rate fields with separately prepared reference outputs. It should reject a phase-space-only submission, a three-phonon-only submission, and a source-figure lookup even if one qualitative label matches. The oracle provides one correct solution path; alternative calculations that reach the same physical quantities pass.

### Shortcut and difficulty audit before release

The author must answer each question using the *actual candidate data* before calling the task qualified:

| Potential shortcut | Design condition that closes it |
| --- | --- |
| Read a source article or bundled conductivity log | Score new condition-specific numerical boundaries and modal rates absent from sources; exclude outcome logs from Agent materials. |
| Infer suppression from a phonon gap or symmetry label alone | Include a regime with suppressed three-phonon phase space but consequential allowed matrix elements or four-phonon rates. |
| Run only a conventional three-phonon workflow | Score a boundary and κ trend that change when four-phonon rates are included. |
| Run a brute-force FourPhonon table without scientific choices | Supply raw observations and a continuous condition range rather than ready-made IFCs and rate tables. The solver must resolve force fitting, convergence, and which modes explain a boundary; a full calculation remains a valid route. If the prepared inputs still make one unexamined batch command sufficient, redesign the item. |
| Guess a mechanism label from the known BP/BAs literature | Require new, model-specific numerical predictions at held-out conditions. |

This is a design test, not a claim that the current archives already meet it.

### Case-selection gate: create real scientific forks

A single smooth crossing is still too close to a parameter sweep. The released condition set must contain several *genuine* competing cases, selected from calculated or measured force models rather than created by multiplying rates in a spreadsheet:

- Two conditions with similar apparent three-phonon phase-space restriction but materially different cubic matrix elements, so phase-space ranking alone gives the wrong rate ranking in one case.
- A condition where three-phonon channels are strongly restricted yet four-phonon scattering changes the heat-carrying lifetimes and κ, and another where the same qualitative restriction leaves four-phonon scattering comparatively unimportant.
- A conspicuous symmetry or dispersion feature that affects a narrow mode set but contributes little to κ, so treating every forbidden triplet as transport-relevant yields the wrong answer.
- At least one condition where the inexpensive rule-based forecast agrees with the full calculation, so the answer is a *domain of validity* rather than a blanket rejection of selection rules.

These are acceptance conditions for choosing the scientific instances. The author must not assert that BP/BAs automatically supply all four; if the actual pressure–temperature series lacks a fork, expand the material set or choose another physically grounded series. The final question should ask for the correct domain and its decisive counterexample, with numerical rate and transport predictions. It should not list these four cases or tell the Agent how to locate them.

## Missing inputs before this becomes a full example

The eight current source archives support the fixed three-phonon coupling demonstration. They do not by themselves establish converged fourth-order force constants, four-phonon scattering rates, or a pressure–temperature series for BP and BAs. Those force observations, compatible fourth-order fitting and scattering software, and a correct answer must be produced before replacing the current `problem.md`. [FourPhonon](https://github.com/FourPhonon/FourPhonon) can calculate both three- and four-phonon rates and conductivity from second-, third-, and fourth-order IFCs; [Fourthorder](https://github.com/FourPhonon/Fourthorder) offers a finite-displacement route to fourth-order IFCs. Other scientific tools may be included so the environment does not dictate a single route. No Agent trial is needed to judge the structural design; human or Agent trials address empirical difficulty after the scientific task exists.

One concrete upstream starting point is FourPhonon's [BAs example input](https://github.com/FourPhonon/FourPhonon/tree/main/Example-BAs/input), which publishes second-, third-, and fourth-order IFCs and a 300 K control file. Its [Si example input](https://github.com/FourPhonon/FourPhonon/tree/main/Example-Si/input) also publishes third- and fourth-order IFCs. These are real fourth-order inputs, unlike the present eight archives. Their public example outputs cannot be scored as-is, and the two examples have not yet been shown to satisfy the competing-case gate above. They are source candidates, not a finished question.

The environment should expose executable, upstream scientific software and its ordinary interfaces: harmonic/symmetry inspection (Phonopy, spglib), third-order rates and transport (Phono3py or ShengBTE), fourth-order fitting and rates (Fourthorder and FourPhonon), and an independent force-constant fitting option such as hiPhive. It should include the associated raw force data and callable calculators where needed. Each tool file records its official source and interface, but no file lays out a task-specific sequence. Existing Agent Skills can be included as optional general capabilities with recorded upstream provenance; they are distinct from the installed scientific tools. All five human-baseline experts receive exactly this environment.

## Sources

- [Ravichandran, *Tuning thermal transport using phonon scattering selection rules* (2026)](https://www.nature.com/articles/s44435-026-00018-1): transition probabilities combine matrix elements, occupation, and conservation; restricted three-phonon channels need not suppress four-phonon channels or transport.
- [Phono3py documentation](https://phonopy.github.io/phono3py/): available three-phonon interactions, scattering rates, and transport calculations.
