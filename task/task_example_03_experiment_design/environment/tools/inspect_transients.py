from pathlib import Path
import pandas as pd, json
root=Path("/workspace/data/raw")
out=[]
for p in root.rglob("*.csv"):
    try:
        df=pd.read_csv(p)
        out.append({"file":str(p.relative_to(root)),"rows":len(df),"columns":list(df.columns),"missing":int(df.isna().sum().sum())})
    except Exception as e:
        out.append({"file":str(p.relative_to(root)),"error":str(e)})
print(json.dumps(out,indent=2))
