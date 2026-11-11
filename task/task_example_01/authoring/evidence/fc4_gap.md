# Source-data coverage audit

The eight retained NIMS archives contain force and displacement data for harmonic and third-order calculations (`phonopy_mlp_eval_fc2_dataset.yaml.xz`, `phono3py_mlp_eval_fc3_disp.yaml.xz`, and `FORCES_FC3.xz`). Inspection of all archive member names found no `FC4`, `FORCES_FC4`, or fourth-order force-constant artifact. Their fitted potentials may permit new calculations, but they are not themselves an independently established fourth-order reference.

Consequences for this item:

- The existing 6₃ selection-rule calculation remains useful evidence about selected three-phonon interactions.
- No four-phonon rate, full lifetime, or three-plus-four-phonon conductivity can be inferred from the present source archives alone.
- The existing `solution/answer.json`, `solution/solve.sh`, and `tests/verify.py` close only the engineering pilot. They do not establish an oracle or verifier for the original scientific problem.
- A complete replacement needs a compatible, versioned FC2/FC3/FC4 set for the same physical models, a four-phonon solver, independent reference calculations, and new answer tolerances. Mixing an unrelated FC4 file with these NIMS FC2/FC3 models would be invalid.

This is a blocking data and oracle gap for final scientific acceptance. The task status in `task.toml` remains `engineering_demo_not_research_qualified`.
