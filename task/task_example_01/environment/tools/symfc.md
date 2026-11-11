# symfc

- Installed: `symfc==1.8.0`; Python module `symfc`.
- Official source: https://github.com/symfc/symfc
- Official interface: https://symfc.github.io/symfc/ (upstream points to `api_symfc.py` for detailed signatures).
- Function: symmetry-constrained second-, third-, and fourth-order force constants from supercell displacements and forces.

**Python interface:** `symfc.Symfc` accepts a supercell plus matching displacement/force arrays; `run(orders=[2, 3])` fits selected orders and `force_constants` exposes tensors keyed by order. `python -c "import inspect, symfc; print(inspect.signature(symfc.Symfc))"` displays the installed constructor. Phonopy and Phono3py also expose symfc as an FC solver through their documented interfaces.

**Input/output:** Consistent atom ordering, array shapes, and force units are required. Output is fitted force-constant tensors, not underlying electronic forces.
