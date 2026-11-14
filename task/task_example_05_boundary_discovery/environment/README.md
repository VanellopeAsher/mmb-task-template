# Agent-visible environment

Build with `docker build -t mmb-task environment`. Inputs are versioned locally; runtime needs no network. Python package versions are pinned in requirements.txt. data/, tools/ and skills/ are the only copied task materials. Author-side source mappings, generation code, answers and verifier are excluded. See data/README.md for scientific limitations.
