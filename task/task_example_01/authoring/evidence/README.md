# Independent evidence

`build_ba_reference.py` validates the mode rate tables, channel sums, gap and RTA outputs from two grids and two independent four-phonon sampling levels. It admits only below-gap acoustic modes that preserve a strong three- or four-phonon dominance margin in all four runs. `inspect_ba_rates.py` supports author-side inspection. The frozen accepted set is `tests/reference_modes.json`; evaluated agents cannot see either file.
