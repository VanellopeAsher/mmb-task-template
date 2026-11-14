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
    point = GOOD['findings']['b_right_1']
    cases.extend([
        ('selected_subset', {'findings': {'b_right_1': point,
                                         'b_left_1': {'status': 'insufficient_evidence'}}}, 1),
        ('different_limitation', {'findings': {'b_right_1': point,
                                              'b_right_2': {'status': 'insufficient_evidence'}}}, 1),
        ('only_deviation', {'findings': {'b_right_1': point}}, 0),
        ('pooled_only_deviation_promoted', altered(['findings', 'b_left_1'], point), 0),
        ('potential_deviation_promoted', altered(['findings', 'b_right_4'], point), 0),
        ('reversed_direction', altered(['findings', 'b_right_1', 'status'], 'lower'), 0),
        ('missed_deviation', altered(['findings', 'b_right_1'], {'status': 'insufficient_evidence'}), 0),
        ('incorrect_coverage', altered(['findings', 'b_right_2'], point), 0),
        ('missing_currents', altered(['findings', 'b_right_1'], {'status': 'higher'}), 0),
        ('wrong_current', altered(['findings', 'b_right_1', 'j_CH4_mA_cm2'], 1), 0),
        ('reading_tolerance', altered(['findings', 'b_right_1', 'j_CH4_mA_cm2'],
                                      point['j_CH4_mA_cm2'] * 10 ** .08), 1),
    ])
    for value in (True, 0, float('nan'), float('inf')):
        cases.append((f'invalid_current_{value}', altered(
            ['findings', 'b_right_1', 'j_CH4_mA_cm2'], value), 0))
    reports = run_cases(cases)
    if args.report:
        args.report.write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(reports)} CLI reward checks passed')
