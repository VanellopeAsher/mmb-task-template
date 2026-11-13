import importlib.metadata as md
import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import linregress
if not np.isclose(linregress([0,1,2],[0,2,4]).slope,2):raise RuntimeError('SciPy regression failed')
if cKDTree(np.array([[0.,0,0],[1,0,0]])).query([.9,0,0])[1]!=1:raise RuntimeError('Spatial query failed')
import pandas,networkx as nx
from ase import Atoms
from pymatgen.core import Lattice,Structure
s=Structure(Lattice.cubic(3),['C'],[[0,0,0]])
if len(s)!=1 or len(Atoms('H2'))!=2 or nx.path_graph(3).number_of_edges()!=2:raise RuntimeError('Structural interfaces failed')
for p in ['numpy','scipy','pandas','ase','pymatgen','networkx']:print(p,md.version(p))
