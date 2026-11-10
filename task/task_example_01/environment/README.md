# Agent environment

`Dockerfile` defines the agent-visible software stack from `requirements.txt`. `data/nims/` contains eight source archives and an agent-visible catalog; `tools/` contains optional inspection and screw-character utilities; `skills/` explains methods, limits, and the output interface. All data are available at task start. The agent can choose among symmetry analysis, force-constant reconstruction, scattering calculations, transport comparisons, and literature synthesis. `solution/`, `tests/`, and `authoring/` are excluded from this image.
