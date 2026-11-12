import csv,json,sys
from pathlib import Path
csvp=Path(__file__).resolve().parents[2]/"environment"/"data"/"candidate_performance.csv"
rows=list(csv.DictReader(csvp.open()))
row=next(r for r in rows if r["mof_id"]=="NIRPAI")
a=json.loads(Path(sys.argv[1]).read_text())
assert abs(float(row["purity"])-a["process_kpis"]["purity"])<1e-9
