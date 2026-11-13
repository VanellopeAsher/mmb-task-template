"""Validate CI plumbing without pretending that an expert awarded full credit."""
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
expected=0.0
for key,target in spec['targets'].items():
    error=abs(answer[spec['field']][key]-target)
    if error<=1e-9:
        error=0.0
    expected += spec['numeric_max']/len(spec['targets'])*max(0,1-error/spec['error_scale'])
def require(value,message):
    if not value:
        raise RuntimeError(message)
if args.harbor_job:
    trials=[p for p in args.harbor_job.rglob('result.json') if p.parent!=args.harbor_job]
    require(len(trials)==1,f'Expected one Harbor trial, got {trials}')
    result=json.loads(trials[0].read_text(encoding='utf-8'))
    require(not result.get('exception_info'),f'Harbor trial exception: {result.get("exception_info")}')
    reward=result.get('verifier_result',{}).get('rewards',{}).get('reward')
else:
    require(args.reward is not None and args.status is not None,'Both --reward and --status are required')
    reward=float(args.reward.read_text(encoding='utf-8'))
    state=json.loads(args.status.read_text(encoding='utf-8'))
    require(state.get('status')=='pending_expert_review',f'Unexpected status: {state}')
    require(state.get('expert_points') is None and state.get('total_points') is None,'Unreviewed run must not claim an expert total')
    require(abs(state['numeric_points']-expected)<1e-8,'Numeric points do not match independent formula')
require(type(reward) in (float,int) and math.isfinite(reward),'Missing or nonfinite reward')
require(abs(reward-expected/100)<1e-8,f'Expected numeric-only reward {expected/100}, got {reward}')
print(json.dumps({'numeric_reward':reward,'expected_numeric_reward':expected/100,'expert_review':'pending','scientific_full_pass':False}))
