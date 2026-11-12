import numpy as np
def pearson_log_current(ch4, c2plus):
    x=np.log10(np.asarray(ch4,dtype=float))
    y=np.log10(np.asarray(c2plus,dtype=float))
    return float(np.corrcoef(x,y)[0,1])
