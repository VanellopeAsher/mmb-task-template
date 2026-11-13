# Agent environment

`Dockerfile` builds the pinned FourPhonon solver with the bundled GNU Fortran compatibility and sampling patch. `data/ba/` contains the released second-, third-, and fourth-order force constants and original upstream control file. NumPy and SciPy support independent output analysis. `tools/fourphonon.md` documents the solver interface and `tools/check_software.py` checks the installed executable and Python modules. The image excludes `solution/`, `tests/`, and `authoring/`.
