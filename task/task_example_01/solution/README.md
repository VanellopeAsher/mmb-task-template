# Reference solution

`solve.sh` recomputes four BAs solver conditions from `/workspace/data/ba/`: 16³ and 20³ with three-phonon scattering only, and the same two grids with both third- and fourth-order scattering. `witness/run_ba.py` sets 350 K, `scalebroad=1.0`, RTA, and the sampled four-phonon path, then `witness/assemble_ba_answer.py` selects two strongly separated below-gap acoustic modes from the common grid points. The final artifact is `/workspace/results/answer.json`.

`answer.json` records one completed 100,000-sample reference run. The executable Oracle uses an independent 10,000-sample run and reports a prevalidated mode pair with lower sampling variance. It computes their rates and transport anew; it does not copy the frozen file. The source calculation and solver patch are documented in `authoring/research_redesign.md` and `environment/fourphonon.patch`. This directory is withheld from evaluated Agents and human experts.
