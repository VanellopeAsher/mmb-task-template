# FourPhonon

- Upstream: https://github.com/FourPhonon/FourPhonon
- Pinned source commit: `5b814b337e03e72907a15a2c953723171fba7102`
- Local build: `/opt/fourphonon/ShengBTE_cpu`, also available as `fourphonon-shengbte`
- License: GPL-3.0
- Build changes: `environment/fourphonon.patch` ports Intel compiler flags to GNU Fortran and starts six random-sampling loops at array index 1. The same patch is applied to the Agent image and author reference runs.

Run the binary inside a directory containing `CONTROL`, `FORCE_CONSTANTS_2ND`, `FORCE_CONSTANTS_3RD`, and `FORCE_CONSTANTS_4TH`. It uses MPI; for example, `OMP_NUM_THREADS=1 mpirun -np 4 fourphonon-shengbte`. Inside a root-run container, OpenMPI also requires `OMPI_ALLOW_RUN_AS_ROOT=1` and `OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1`.

The output includes `BTE.qpoints` (irreducible q points, last three columns are reciprocal coordinates), `BTE.omega` (q-major branch frequencies), and per-temperature `BTE.w_3ph`, `BTE.w_4ph`, channel rates, and `BTE.kappa_scalar`. Rate files are **branch-major**: all q points for branch 1, then branch 2, and so on. The first rate column is frequency in rad/ps; the second is total rate in ps⁻¹. The `BTE.kappa_scalar` row indexed `0` is the RTA value. Check the solver log for `Info: normal exit` before using outputs.
