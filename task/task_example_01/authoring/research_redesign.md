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

The author should first build a material/condition set containing at least one regime in which a selection-rule prediction survives explicit rate and transport calculations and at least one regime in which it fails for an identified physical reason. The solver would return an `answer.json` with a condition-dependent boundary or classification, quantitative dominant-channel fractions for heat-carrying modes, and a transport consequence at specified held-out conditions. The task statement must define the answer fields, units, tolerances, and what counts as a dominant channel, without prescribing the experiments used to infer them.

The independent verifier should recompute or compare against independently prepared three- and four-phonon rates and conductivity data, then score the boundary and numerical predictions. A mechanism label alone should earn no full score. Its ground truth must be sensitive to the distinction between phase space and matrix elements and to the inclusion of four-phonon scattering. The oracle provides one correct solution path; the task need not require that path.

## Missing inputs before this becomes a full example

The eight current source archives support the fixed three-phonon coupling demonstration. They do not by themselves establish converged fourth-order force constants, four-phonon scattering rates, or a condition series that crosses a rule's predictive boundary. These inputs and a compatible four-phonon calculation tool must be sourced or generated, versioned, and kept accessible to both Agent and human experts. The author must establish a correct answer and verifier before replacing the current `problem.md`. No experimental trial is needed to decide that the *current* design fails the structural gate; human or Agent trials address empirical difficulty only after a scientifically qualified task exists.

## Sources

- [Ravichandran, *Tuning thermal transport using phonon scattering selection rules* (2026)](https://www.nature.com/articles/s44435-026-00018-1): transition probabilities combine matrix elements, occupation, and conservation; restricted three-phonon channels need not suppress four-phonon channels or transport.
- [Phono3py documentation](https://phonopy.github.io/phono3py/): available three-phonon interactions, scattering rates, and transport calculations.
