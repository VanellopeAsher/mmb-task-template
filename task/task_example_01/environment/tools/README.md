# Available tool

`inspect_nims.py` is a general reader for the supplied NIMS ZIP archives. It lists archive members, reads crystal structures and temperature-dependent conductivity tensors, and extracts archive members. Its CLI exposes `--help`. `check_software.py` imports installed scientific packages and locates installed CLIs, returning a nonzero exit status if a required component is unavailable.

The installed scientific software is listed in `../requirements.txt`. The source archives also contain polynomial potential parameters and VASP input records. VASP is not installed.
