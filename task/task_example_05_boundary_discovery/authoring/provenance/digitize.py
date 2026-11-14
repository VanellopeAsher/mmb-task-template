from pathlib import Path
import csv,json,hashlib
import numpy as np
from PIL import Image
import argparse,fitz,tempfile
p=argparse.ArgumentParser();p.add_argument('--paper',type=Path,required=True);args=p.parse_args()
if hashlib.sha256(args.paper.read_bytes()).hexdigest()!='37ef0d91b27b2d3b433826ea0f650c58ed3f863f39de8f9d140e7e06b161bdba': raise ValueError('Source SHA256 mismatch')
doc=fitz.open(args.paper);image_bytes=doc.extract_image(doc[2].get_images()[0][0])['image']
root=Path(__file__).resolve().parents[2];out=root/'environment/data';out.mkdir(exist_ok=True)
# First independent manual center readings of original embedded Figure 2 (1950 x 1888).
# Label, composition, additive, pixel x, methane y, C2+ y, panel.
rows=[]
for comp,add,panel,points in [
 ('Cu0.98Mn0.02','none','a_left',[(233,96,94),(266,115,109),(315,164,164)]),
 ('Cu0.84Mn0.16','none','a_right',[(692,120,112),(743,147,132),(795,234,222),(879,257,246),(968,245,236)]),
 ('Cu0.98Mn0.02','1-Br2','b_left',[(203,441,349),(253,467,360),(277,510,391),(355,550,470),(462,571,514)]),
 ('Cu0.84Mn0.16','1-Br2','b_right',[(725,441,356),(746,494,379),(806,548,403),(871,558,442),(942,560,459),(974,573,470)])]:
 for j,(x,ch,c2) in enumerate(points,1):
  rows.append(dict(condition_id=f'{panel}_{j}',composition=comp,additive=add,panel=panel,x=x,ch4_y=ch,c2plus_y=c2))
cal={'a_left':dict(x0=201,x1=450,E0=-1.1,E1=-.9,y0=302,y1=60),
     'a_right':dict(x0=618,x1=991,E0=-1.1,E1=-.8,y0=302,y1=60),
     'b_left':dict(x0=201,x1=450,E0=-1.1,E1=-.9,y0=575,y1=333),
     'b_right':dict(x0=618,x1=991,E0=-1.1,E1=-.8,y0=575,y1=333)}
# Second extraction: color segmentation around each manually located marker,
# independent centroid coordinates, not a human independent observer.
im=np.array(Image.open(__import__('io').BytesIO(image_bytes)).convert('RGB')).astype(float)
records=[];public=[]
# Candidate marker centers in Figure 2c by legend identity, not by row order.
baseline_markers = {
    'Cu0.98Mn0.02': [(1827, 88), (1716, 207), (1872, 58)],
    'Cu0.84Mn0.16': [(1548, 362), (1825, 96), (1520, 382), (1759, 137), (1573, 330)],
}
matched_markers = set()
for row in rows:
 c=cal[row['panel']]; reread={}
 for key,color in ([] if row['additive']=='none' else [('ch4_y',np.array([185,80,20])),('c2plus_y',np.array([255,20,40]))]):
  x,y=row['x'],row[key];patch=im[y-7:y+8,x-7:x+8];mask=np.linalg.norm(patch-color,axis=2)<65
  yy,xx=np.where(mask)
  if len(yy)<3: raise ValueError((row,key))
  reread[key]=float(np.median(yy)+y-7)
 logs={k:-3+(c['y0']-row[k])*4/(c['y0']-c['y1']) for k in ['ch4_y','c2plus_y']}
 if row['additive']=='none':
  panel_a_logs = logs.copy()
  candidates = []
  for px, py in baseline_markers[row['composition']]:
   candidate_logs = {'ch4_y': -3+(px-1423)/395*3, 'c2plus_y': -3+(506-py)/396*3}
   discrepancies = {key: abs(candidate_logs[key]-panel_a_logs[key]) for key in candidate_logs}
   if max(discrepancies.values()) <= .08:
    candidates.append(((px, py), candidate_logs, discrepancies))
  if len(candidates) != 1:
   raise ValueError(f"Ambiguous cross-panel identity for {row['condition_id']}: {candidates}")
  (bx, by), logs, discrepancies = candidates[0]
  if (bx, by) in matched_markers:
   raise ValueError('Figure 2c marker matched more than once')
  matched_markers.add((bx, by))
  row['cross_panel_identity'] = dict(panel_a_approximate_log10=panel_a_logs,
                                    panel_c_log10=logs, absolute_log10_difference=discrepancies)
  color=np.array([255,20,20] if row['composition']=='Cu0.98Mn0.02' else [255,143,85])
  patch=im[by-7:by+8,bx-7:bx+8];mask=np.linalg.norm(patch-color,axis=2)<65
  yy,xx=np.where(mask)
  if len(xx)<3: raise ValueError(row)
  errors={'ch4_y':abs(float(np.median(xx)+bx-7)-bx)/395*3,'c2plus_y':abs(float(np.median(yy)+by-7)-by)/396*3}
  reread={'x':float(np.median(xx)+bx-7),'y':float(np.median(yy)+by-7)}
  row['paired_panel_c_pixel']=[bx,by]
 else: errors={k:abs(reread[k]-row[k])*4/(c['y0']-c['y1']) for k in reread}
 records.append(dict(**row,second_read_y=reread,absolute_log10_disagreement=errors))
 public.append(dict(condition_id=row['condition_id'],composition=row['composition'],additive=row['additive'],
   electrolyte_M=.1,potential_V_RHE=round(c['E0']+(row['x']-c['x0'])*(c['E1']-c['E0'])/(c['x1']-c['x0']),4),
   j_CH4_mA_cm2=round(10**logs['ch4_y'],7),j_C2plus_mA_cm2=round(10**logs['c2plus_y'],7),
   log10_reading_bound=.08,source_locator=('Figure 2c currents; Figure 2'+row['panel']+' potential' if row['additive']=='none' else 'Figure 2'+row['panel'])))
with (out/'observations.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=public[0],lineterminator="\n");w.writeheader();w.writerows(public)
p=root/'authoring/evidence/digitization.json'
p.write_text(json.dumps(dict(source_pdf_sha256='37ef0d91b27b2d3b433826ea0f650c58ed3f863f39de8f9d140e7e06b161bdba',
 image_sha256=hashlib.sha256(image_bytes).hexdigest(),image_size=[1950,1888],cross_panel_match_limit_dex=.08,calibration=dict(**cal,panel_c=dict(x_minus3=1423,x_zero=1818,y_minus3=506,y_zero=110)),readings=records,
 max_log10_disagreement=max(v for r in records for v in r['absolute_log10_disagreement'].values())),indent=2)+'\n')
print('rows',len(public),'maximum reread disagreement',max(v for r in records for v in r['absolute_log10_disagreement'].values()))
