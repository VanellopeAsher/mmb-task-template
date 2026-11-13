"""Actual CLI reward tests, including optimized Python and malformed inputs."""
import argparse,copy,json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
GOOD=json.loads((HERE.parent/'solution/answer.json').read_text(encoding='utf-8'))

def altered(path,value):
    x=copy.deepcopy(GOOD);p=x
    for part in path[:-1]:p=p[part]
    p[path[-1]]=value
    return x

def run_cases(cases):
    reports=[]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);answer=root/'answer.json';reward=root/'reward.txt'
        for optimized in [False,True]:
            for name,payload,expected in cases:
                if answer.exists():answer.unlink()
                if payload is not None:answer.write_text(json.dumps(payload),encoding='utf-8')
                command=[sys.executable]+(['-O'] if optimized else [])+[str(HERE/'verify.py'),'--answer',str(answer),'--reward',str(reward)]
                r=subprocess.run(command,capture_output=True,text=True,check=True)
                actual=float(reward.read_text())
                if actual!=expected:raise RuntimeError(f'{name}, optimized={optimized}: reward {actual}, expected {expected}: {r.stdout}')
                details = json.loads(reward.with_name('assessment.json').read_text(encoding='utf-8'))
                if details['reward'] != expected:
                    raise RuntimeError(f'{name}: reward and diagnostics disagree')
                failed = sorted(key for key, value in details['sections'].items() if not value['passed'])
                isolated = {
                    'pooled_promoted_to_matched': ['matched_methane'],
                    'methane_promoted_to_potential': ['matched_potential'],
                }
                if name in isolated and failed != isolated[name]:
                    raise RuntimeError(f'{name}: unexpected failed sections {failed}')
                reports.append(dict(case=name,optimized=optimized,reward=actual,failed_sections=failed))
        answer.write_text('{invalid',encoding='utf-8')
        subprocess.run([sys.executable,str(HERE/'verify.py'),'--answer',str(answer),'--reward',str(reward)],check=True,capture_output=True)
        if reward.read_text().strip()!='0':raise RuntimeError('Malformed JSON accepted')
        reports.append(dict(case='malformed_json',reward=0))
    return reports

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    cases = [
        ('oracle', GOOD, 1),
        ('analysis_unscored', dict(GOOD, analysis='arbitrary'), 1),
        ('missing', None, 0),
        ('empty', {}, 0),
        ('array', [], 0),
    ]
    alternate = json.loads((HERE.parent / 'authoring/evidence/alternative_answer.json').read_text(encoding='utf-8'))
    cases.append(('alternative', alternate, 1))

    catalog = json.loads((HERE / 'condition_context.json').read_text(encoding='utf-8'))
    window = ['matched_methane', 'b_right_1']
    pair = GOOD[window[0]][window[1]]['controls']
    margin = GOOD[window[0]][window[1]]['margin_dex']
    cases.extend([
        ('margin_at_tolerance', altered(window + ['margin_dex'], margin + .02), 1),
        ('margin_outside_tolerance', altered(window + ['margin_dex'], margin + .020001), 0),
        ('margin_bool', altered(window + ['margin_dex'], True), 0),
        ('margin_nan', altered(window + ['margin_dex'], float('nan')), 0),
        ('margin_infinity', altered(window + ['margin_dex'], float('inf')), 0),
        ('margin_wrong_units', altered(window + ['margin_dex'], 10 ** margin), 0),
        ('contradictory_direction', altered(window + ['status'], 'lower'), 0),
        ('no_endpoints', altered(window, {'status': 'higher', 'margin_dex': margin}), 0),
        ('endpoint_order_reversed', altered(window + ['controls'], pair[::-1]), 0),
        ('same_endpoint_twice', altered(window + ['controls'], [pair[0], pair[0]]), 0),
        ('film_as_control', altered(window + ['controls'], [pair[0], 'b_right_2']), 0),
        ('pooled_promoted_to_matched',
         altered(['matched_methane', 'b_left_1'], GOOD['pooled_methane']['b_left_1']), 0),
        ('methane_promoted_to_potential', altered(['matched_potential', 'b_right_1'], GOOD['matched_methane']['b_right_1']), 0),
        ('potential_promoted_to_methane', altered(['matched_methane', 'b_right_4'], GOOD['matched_potential']['b_right_4']), 0),
        ('out_of_range_endpoints', altered(window + ['controls'], ['a_right_4', 'a_right_5']), 0),
        ('outside_called_unresolved', altered(['matched_methane', 'b_left_1', 'status'], 'unresolved'), 0),
        ('inside_called_outside', altered(['matched_methane', 'b_right_2', 'status'], 'outside_support'), 0),
        ('window_below_effect_threshold',
         altered(['matched_methane', 'b_right_2'], dict(status='higher', controls=['a_right_3', 'a_right_2'],
                                                       margin_dex=.2842148627)), 0),
        ('only_regression_coefficients', {'baseline': {'slope': .93, 'intercept': 0}}, 0),
        ('only_methane', {'matched_methane': GOOD['matched_methane']}, 0),
    ])
    for name, choices in catalog['matched_methane'].items():
        if len(choices) > 1:
            cases.append((f'different_valid_window_{name}', altered(['matched_methane', name], choices[-1]), 1))
    reports = run_cases(cases)
    if args.report:
        args.report.write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(reports)} CLI reward checks passed')
