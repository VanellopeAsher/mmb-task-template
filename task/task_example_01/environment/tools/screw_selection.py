"""Evaluate a restricted screw-axis character-product selection condition.

For an n_p screw with translation p/n of the axial lattice vector, a
nondegenerate mode on the invariant line has an eigenvalue proportional to
exp[2*pi*i*(m/n - p*q_z/n)]. For a 1+2->3 process with axial reciprocal
vector G_z = q1+q2-q3, invariance requires
    m1 + m2 - m3 - p*G_z == 0 (mod n).
This is a necessary symmetry condition, not a sufficient condition for a
nonzero scattering rate or a prediction of thermal conductivity. Degenerate
mode subspaces require representation analysis rather than scalar labels.
"""

from __future__ import annotations

import argparse
import json


def allowed(n: int, p: int, m1: int, m2: int, m3: int, g_z: int) -> bool:
    if n < 2 or not 0 < p < n:
        raise ValueError("Expected a screw n_p with n >= 2 and 0 < p < n")
    return (m1 + m2 - m3 - p * g_z) % n == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True, help="Rotation order")
    parser.add_argument("--p", type=int, required=True, help="Screw translation numerator")
    parser.add_argument("--m1", type=int, required=True, help="First mode screw label")
    parser.add_argument("--m2", type=int, required=True, help="Second mode screw label")
    parser.add_argument("--m3", type=int, required=True, help="Third mode screw label")
    parser.add_argument("--g-z", type=int, required=True, help="Axial reciprocal-lattice index")
    args = parser.parse_args()
    print(json.dumps({"symmetry_allowed": allowed(args.n, args.p, args.m1, args.m2, args.m3, args.g_z)}))


if __name__ == "__main__":
    main()
