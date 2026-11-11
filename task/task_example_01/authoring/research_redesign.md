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

The scientific task would ask for the **domain in pressure and temperature where a dispersion/selection-rule inference correctly identifies the dominant resistance to heat transport, and the first boundary where it fails**. The solver must determine which heat-carrying modes matter, inspect allowed channels and phase space, obtain actual three- and four-phonon rates, and compare the resulting lifetimes and thermal conductivity. A BP/BAs contrast can expose two plausible but wrong explanations for a similar shape of κ(P): the change in acoustic three-phonon channels and the opposing higher-order response. The problem statement should give the physical question and answer contract, not the diagnostic sequence.

### Answer contract

For each material and one declared temperature interval, `answer.json` would report:

- The pressure interval or crossing pressure at which a **transport-weighted** four-phonon rate fraction crosses a fixed dominance threshold. The author must define the mode weights and threshold before releasing the task; use the same definition in the oracle and verifier.
- The pressure and value of the extremum of full thermal conductivity, and the sign of the corresponding three-phonon-only conductivity trend. This tests whether the rule-based trend survives the higher-order calculation.
- Quantitative rates for a small set of held-out heat-carrying mode bins near the boundary, together with a mechanism classification for the discrepancy. A category alone cannot pass if the numbers are wrong.

These fields must be tied to the *same* physical force model and temperature convention. Numerical tolerances should come from pre-established mesh, force-constant, and sampling convergence, not from a convenient scoring margin. The actual values cannot be filled into this design document without the underlying calculations.

One objective definition of “dominant for heat transport” is available within a common single-mode relaxation-time approximation. For each mode λ and transport direction e, compute `γ3(λ)`, `γ4(λ)`, and the modal conductivity weight `w(λ) ∝ C(λ)[v(λ)·e]^2/[γ3(λ)+γ4(λ)]`, normalized over modes. Then `F4 = Σλ w(λ) γ4(λ)/[γ3(λ)+γ4(λ)]`. A crossing of `F4 = 0.5` is a reproducible *rate-dominance* boundary, not by itself a claim about causality. Separately score the actual conductivity impact `D4 = 1 - κ3+4/κ3` and the sign of the pressure derivative of each conductivity. Requiring both prevents a high four-phonon fraction in irrelevant modes from masquerading as a transport mechanism. This definition must be frozen before reference calculations and published in the answer contract; it does not tell the solver which numerical route to use.

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

## Missing inputs before this becomes a full example

The eight current source archives support the fixed three-phonon coupling demonstration. They do not by themselves establish converged fourth-order force constants, four-phonon scattering rates, or a pressure–temperature series for BP and BAs. Those force observations, compatible fourth-order fitting and scattering software, and a correct answer must be produced before replacing the current `problem.md`. [FourPhonon](https://github.com/FourPhonon/FourPhonon) can calculate both three- and four-phonon rates and conductivity from second-, third-, and fourth-order IFCs; [Fourthorder](https://github.com/FourPhonon/Fourthorder) offers a finite-displacement route to fourth-order IFCs. Other scientific tools may be included so the environment does not dictate a single route. No Agent trial is needed to judge the structural design; human or Agent trials address empirical difficulty after the scientific task exists.

## Sources

- [Ravichandran, *Tuning thermal transport using phonon scattering selection rules* (2026)](https://www.nature.com/articles/s44435-026-00018-1): transition probabilities combine matrix elements, occupation, and conservation; restricted three-phonon channels need not suppress four-phonon channels or transport.
- [Phono3py documentation](https://phonopy.github.io/phono3py/): available three-phonon interactions, scattering rates, and transport calculations.
