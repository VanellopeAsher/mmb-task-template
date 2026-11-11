# Scientific software available in the shared image

Each linked file describes one installed upstream package: official source, installed version, callable interface, inputs and outputs. These are interface references, not a research sequence. The same image is used for the agent and human baseline.

| Software | Interface file | Capability |
| --- | --- | --- |
| Phonopy | [phonopy.md](phonopy.md) | Harmonic phonons |
| Phono3py | [phono3py.md](phono3py.md) | Anharmonic phonons and thermal transport |
| spglib | [spglib.md](spglib.md) | Crystal symmetry |
| symfc | [symfc.md](symfc.md) | Symmetric force-constant fitting |
| SeeK-path | [seekpath.md](seekpath.md) | Reciprocal-space paths |
| pypolymlp | [pypolymlp.md](pypolymlp.md) | Polynomial interatomic potentials |
| hiPhive | [hiphive.md](hiphive.md) | High-order force constants |
| pymatgen | [pymatgen.md](pymatgen.md) | Materials structures and formats |
| ASE | [ase.md](ase.md) | Atomistic structures and calculators |
| Materials Project API | [mp-api.md](mp-api.md) | Online materials records; personal API key required |

`inspect_nims.py` reads and extracts supplied NIMS ZIP members (`python /workspace/tools/inspect_nims.py --help`). `check_software.py` checks package imports and CLIs. They are task utilities, not the scientific software itself. The source archives contain VASP input records, but VASP is not installed.
