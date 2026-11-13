"""Regression checks for the current numeric + pending-expert contract.
These are synthetic test fixtures, not real expert evaluations.
Run with both ordinary Python and python -O.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
SPEC = json.loads((HERE/'targets.json').read_text(encoding='utf-8'))
GOOD = json.loads((TASK/'solution/answer.json').read_text(encoding='utf-8'))
IS03 = SPEC['field']=='predicted_recovery'

def expected_points(payload):
    total = 0.0
    for key,target in SPEC['targets'].items():
        error = abs(payload[SPEC['field']][key]-target)
        if error<=1e-9:
            error=0.0
        total += SPEC['numeric_max']/len(SPEC['targets'])*max(0.0,1-error/SPEC['error_scale'])
    return total

class ContractChecks(unittest.TestCase):
    def execute(self,payload,review=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            answer=root/'answer.json'
            answer.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=True),encoding='utf-8')
            review_file=root/'review.json'
            if review is not None:
                record=deepcopy(review)
                if record.pop('bind_current_answer',False):
                    record['answer_sha256']=hashlib.sha256(answer.read_bytes()).hexdigest()
                review_file.write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
            reward=root/'reward.txt'
            command=[sys.executable]
            if sys.flags.optimize:
                command.append('-O')
            command += [str(HERE/'verify.py'),'--answer',str(answer),'--reward',str(reward),'--review-file',str(review_file)]
            proc=subprocess.run(command,capture_output=True,text=True)
            self.assertTrue(reward.exists(),proc.stderr)
            numeric=json.loads(reward.with_suffix('.json').read_text(encoding='utf-8'))
            self.assertEqual(set(numeric),{'reward'})
            self.assertIn(type(numeric['reward']),(int,float))
            self.assertTrue(math.isfinite(numeric['reward']))
            self.assertEqual(numeric['reward'],float(reward.read_text()))
            details=reward.with_name(reward.stem+'_details.json')
            self.assertTrue(details.exists())
            return proc.returncode,float(reward.read_text()),json.loads(details.read_text(encoding='utf-8'))

    def reject(self,payload,review=None):
        code,reward,result=self.execute(payload,review)
        self.assertNotEqual(code,0)
        self.assertEqual(reward,0.0)
        self.assertEqual(result['status'],'invalid')

    def test_reference_pending_and_exact_numeric_score(self):
        code,reward,result=self.execute(GOOD)
        self.assertEqual(code,0)
        self.assertEqual(result['status'],'pending_expert_review')
        self.assertAlmostEqual(result['numeric_points'],expected_points(GOOD),places=10)
        self.assertAlmostEqual(reward,expected_points(GOOD)/100,places=8)
        self.assertIsNone(result['expert_points'])
        self.assertIsNone(result['total_points'])

    def test_perfect_numbers_are_not_full_scientific_credit(self):
        good=deepcopy(GOOD)
        good[SPEC['field']]=deepcopy(SPEC['targets'])
        code,reward,result=self.execute(good)
        self.assertEqual(code,0)
        self.assertAlmostEqual(reward,SPEC['numeric_max']/100)
        self.assertEqual(result['numeric_points'],SPEC['numeric_max'])
        self.assertIsNone(result['total_points'])

    def test_error_formula_and_zero_boundary(self):
        for fraction in (0.25,0.5,1.0,2.0):
            candidate=deepcopy(GOOD)
            candidate[SPEC['field']]={k:v+fraction*SPEC['error_scale'] for k,v in SPEC['targets'].items()}
            code,reward,result=self.execute(candidate)
            self.assertEqual(code,0)
            self.assertAlmostEqual(result['numeric_points'],SPEC['numeric_max']*max(0,1-fraction),places=8)

    def test_numeric_precision_floor(self):
        candidate=deepcopy(GOOD)
        candidate[SPEC['field']]={k:v+1e-10 for k,v in SPEC['targets'].items()}
        self.assertEqual(self.execute(candidate)[2]['numeric_points'],SPEC['numeric_max'])

    def test_invalid_numbers(self):
        key=next(iter(SPEC['targets']))
        for bad in (True,None,'0.8',[],{},float('nan'),float('inf'),-float('inf')):
            with self.subTest(bad=repr(bad)):
                candidate=deepcopy(GOOD)
                candidate[SPEC['field']][key]=bad
                self.reject(candidate)

    def test_missing_and_extra_fields(self):
        self.reject({})
        self.reject([])
        for key in GOOD:
            candidate=deepcopy(GOOD)
            del candidate[key]
            self.reject(candidate)
        self.reject(dict(GOOD,analysis='old unscored field is no longer in the contract'))
        candidate=deepcopy(GOOD)
        candidate[SPEC['field']]['unexpected']=0
        self.reject(candidate)
        candidate=deepcopy(GOOD)
        del candidate[SPEC['field']][next(iter(SPEC['targets']))]
        self.reject(candidate)

    def test_report_required(self):
        for report in ('','  ',None,[],42):
            self.reject(dict(GOOD,scientific_report=report))

    def test_experiment_choices(self):
        if not IS03:
            self.skipTest('Fourth task has no selected_experiment field')
        for choice in 'ABCD':
            code,reward,result=self.execute(dict(GOOD,selected_experiment=choice))
            self.assertEqual(code,0)
            self.assertEqual(result['status'],'pending_expert_review')
            self.assertAlmostEqual(result['numeric_points'],expected_points(GOOD))
        for choice in ('E','A+B',['A','B'],None,True,''):
            self.reject(dict(GOOD,selected_experiment=choice))

    def test_synthetic_review_hash_binding_and_bounds(self):
        # Exercises the merge mechanism only. This record is never stored as a real review.
        record={'bind_current_answer':True,'reviewer':'SYNTHETIC_TEST_ONLY','rationale':'Unit fixture; not a scientific assessment.',
                'scores':{k:v/2 for k,v in SPEC['expert_components'].items()}}
        code,reward,result=self.execute(GOOD,record)
        self.assertEqual(code,0)
        self.assertEqual(result['status'],'reviewed')
        self.assertAlmostEqual(result['total_points'],expected_points(GOOD)+sum(record['scores'].values()))
        stale=deepcopy(record)
        stale.pop('bind_current_answer')
        stale['answer_sha256']='0'*64
        self.reject(GOOD,stale)
        excessive=deepcopy(record)
        first=next(iter(SPEC['expert_components']))
        excessive['scores'][first]=SPEC['expert_components'][first]+1
        self.reject(GOOD,excessive)
        boolean=deepcopy(record)
        boolean['scores'][first]=True
        self.reject(GOOD,boolean)

    def test_targets_recompute_from_separate_held_out_evidence(self):
        if IS03:
            visible=json.loads((TASK/'environment/data/observations.json').read_text(encoding='utf-8'))
            hidden=json.loads((TASK/'authoring/evidence/held_out/24h.json').read_text(encoding='utf-8'))
            calculated={k:(v-visible['power'][k]['0h'])/(visible['power'][k]['origin']-visible['power'][k]['0h']) for k,v in hidden.items()}
        else:
            calculated={}
            for key in 'CDE':
                trace=json.loads((TASK/'authoring/evidence/held_out'/f'{key}_dilute.json').read_text(encoding='utf-8'))
                amount=sum(s['moles_out [mol]'] for s in trace['steps_desorption'])
                methane=sum(s['moles_out [mol]']*s['column_state']['mole_fraction_gas [mol]'][0] for s in trace['steps_desorption'])
                calculated[key]=methane/amount/trace['feed']['mole_fractions'][0]
        for key,value in calculated.items():
            self.assertAlmostEqual(SPEC['targets'][key],value,places=12)

if __name__=='__main__':
    unittest.main(verbosity=2)
