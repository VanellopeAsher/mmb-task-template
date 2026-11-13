# Scientific basis for Example 01

## Question and model

The task tests whether an acoustic–optical gap condition alone identifies the dominant total scattering order of below-gap acoustic modes. It uses the published FourPhonon BAs force model at commit `5b814b337e03e72907a15a2c953723171fba7102`, but asks for a new 350 K calculation on 16³ and 20³ reciprocal meshes with `scalebroad=1.0`. The force constants are real upstream model inputs, not measurements. The upstream 300 K output is not the target answer.

The solver patch ports the pinned source to GNU Fortran and starts all six fourth-order sampling loops at one. The original loops indexed the random array before its first element; sampled rates from that binary are invalid. The exact input checksums and the distinction between upstream `CONTROL` and task conditions are recorded in `environment/data/README.md`.

## Independent numerical evidence

Corrected 100,000-sample fourth-order runs exited normally at 350 K. The 16³ and 20³ RTA conductivities with both scattering orders are 668.94 and 678.67 W/(m·K), a 1.45% mesh difference. Matched three-only calculations give 1101.57 and 1129.69 W/(m·K). Fourth-order scattering therefore lowers RTA conductivity by 39.27% and 39.92%, respectively.

Mode acceptance uses both meshes and independent 10,000- and 100,000-sample runs. `evidence/build_ba_reference.py` checks branch-major rate ordering against harmonic frequencies, verifies the three-channel and four-channel rate sums, restricts to acoustic modes below the gap, and retains only modes whose four/three rate ratio is at most 0.4 in all runs or at least 2.0 in all runs. Ten modes satisfy this rule. One robust three-dominated example is q=(1/4,0,0), branch 1, with ratios near 0.10–0.13. One robust four-dominated example is q=(3/4,1/2,1/4), branch 2, with ratios about 3.83–4.33. Both lie below the gap cutoff near 54.5 rad/ps, directly falsifying the claim that the gap condition by itself determines the dominant total scattering order.

The accepted set is frozen in `tests/reference_modes.json`. The verifier admits any supported opposing pair and checks independently reported rates on both meshes. It does not require the two examples above.

## Scope and remaining validation

The numerical result concerns this force model, temperature, broadening, sampled solver, and RTA definition. It does not establish a universal selection rule or experimental BAs conductivity. At 300 K, the upstream published process counts correspond to `scalebroad=1.0` even though the checked-in `CONTROL` says 0.1. A corrected 100,000-sample reproduction has about 3.01% median and 10.0% 95th-percentile fourth-order mode-rate error against that public output, but its RTA conductivity differs by 5.13%. The benchmark therefore uses independently run 350 K outputs rather than calibrating tolerances against the historical 300 K conductivity.

The Docker/Harbor end-to-end run and real Agent and expert trials must be reported separately. No simulated expert record is used as evidence of human difficulty.
