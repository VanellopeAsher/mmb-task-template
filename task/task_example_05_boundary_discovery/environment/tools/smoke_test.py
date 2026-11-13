import importlib.metadata as md
import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import linregress
if not np.isclose(linregress([0,1,2],[0,2,4]).slope,2):raise RuntimeError('SciPy regression failed')
if cKDTree(np.array([[0.,0,0],[1,0,0]])).query([.9,0,0])[1]!=1:raise RuntimeError('Spatial query failed')
import pandas,matplotlib,statsmodels.api,pymupdf,pdfplumber,cv2
for p in ['numpy','scipy','pandas','matplotlib','statsmodels','pymupdf','pdfplumber','opencv-python-headless']:print(p,md.version(p))
