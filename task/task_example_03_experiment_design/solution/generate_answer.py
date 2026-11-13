"""Generate a candidate answer using visible data only; no held-out reads."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=Path('/workspace/results/answer.json'))
parser.add_argument('--data-dir', type=Path, default=HERE/'witness')
args = parser.parse_args()
visible = json.loads((args.data_dir/'observations.json').read_text(encoding='utf-8'))
predictions = {}
for key in ('a', 'c'):
    power = visible['power'][key]
    estimate = 2*power['18h']-power['12h']
    predictions[key] = (estimate-power['0h'])/(power['origin']-power['0h'])
payload = {'selected_experiment':'B', 'predicted_recovery':predictions,
           'scientific_report':(HERE/'submission_report.md').read_text(encoding='utf-8')}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
