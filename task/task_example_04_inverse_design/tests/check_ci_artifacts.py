"""Validate CI artifacts against the automatic score."""
from verify import score
import argparse
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--answer',type=Path,default=HERE.parent/'solution/answer.json')
parser.add_argument('--reward',type=Path)
parser.add_argument('--status',type=Path)
parser.add_argument('--harbor-job',type=Path)
args=parser.parse_args()
spec=json.loads((HERE/'targets.json').read_text(encoding='utf-8'))
answer=json.loads(args.answer.read_text(encoding='utf-8'))
expected = sum(score(answer).values())
def require(value,message):
    if not value:
        raise RuntimeError(message)
if args.harbor_job:
    trials=[p for p in args.harbor_job.rglob('result.json') if p.parent!=args.harbor_job]
    require(len(trials)==1,f'Expected one Harbor trial, got {trials}')
    result=json.loads(trials[0].read_text(encoding='utf-8'))
    require(not result.get('exception_info'),f'Harbor trial exception: {result.get("exception_info")}')
    reward=result.get('verifier_result',{}).get('rewards',{}).get('reward')
    details=trials[0].parent/'verifier/reward_details.json'
    require(details.is_file(),f'Missing independent evaluation details: {details}')
    state=json.loads(details.read_text(encoding='utf-8'))
else:
    require(args.reward is not None and args.status is not None,'Both --reward and --status are required')
    reward=float(args.reward.read_text(encoding='utf-8'))
    state=json.loads(args.status.read_text(encoding='utf-8'))
require(state.get('status') == 'automatically_scored', 'Expected automatic scoring')
require(abs(state['total_points'] - expected) < 1e-8, 'Section totals disagree')
require(type(reward) in (int, float) and math.isfinite(reward), 'Invalid reward')
require(abs(reward - expected / 100) < 1e-8, 'Unexpected Oracle reward')
print(json.dumps({'automatic_reward': reward, 'expected': expected / 100}))
