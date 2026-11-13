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
                    'same_rank_used_as_counterexample': ['counterexample_selection'],
                    'oblique_axis_flags_only': ['periodic_connectivity'],
                    'correct_ranks_false_full_coverage': ['periodic_connectivity'],
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

    axes = json.loads((HERE / 'axis_reference.json').read_text(encoding='utf-8'))
    cases.extend([
        ('wrong_family', altered(['samples', 'sample_10', 'defect_type'], 'missing_linker'), 0),
        ('wrong_count', altered(['samples', 'sample_10', 'missing_site_count'], 108), 0),
        ('percentage_as_count', altered(['samples', 'sample_10', 'missing_site_count'], 25), 0),
        ('float_count', altered(['samples', 'sample_10', 'missing_site_count'], 27.0), 0),
        ('zero_repeats_imply_no_organization', altered(['samples', 'sample_01', 'spatial'], {'random': True}), 0),
        ('repeat_claimed_without_full_overlap', altered(['samples', 'sample_02', 'spatial'], {'full_repeat_axes': 1}), 0),
        ('repeat_counts_reordered', altered(['samples', 'sample_08', 'spatial'], {'overlap_counts': [36, 0, 36]}), 1),
        ('boolean_repeat_count', altered(['samples', 'sample_01', 'spatial'], {'full_repeat_axes': False}), 0),
        ('incorrect_repeat_profile', altered(['samples', 'sample_02', 'spatial'], {'overlap_counts': [83, 91, 103]}), 0),
        ('ignored_periodic_edges', altered(['samples', 'sample_05', 'connectivity', 'components'], [0]), 0),
        ('oblique_axis_flags_only', altered(['samples', 'sample_12', 'connectivity'],
                                           {'method': 'axis_spans', 'components': axes['sample_12']}), 0),
        ('wrong_oblique_rank', altered(['samples', 'sample_12', 'connectivity', 'components'], [1]), 0),
        ('correct_ranks_false_full_coverage', altered(['samples', 'sample_13', 'network_status'], 'single_3d_network'), 0),
        ('omit_isolated_clusters', altered(['samples', 'sample_13', 'connectivity', 'components'], [3]), 0),
        ('rank_components_reordered', altered(['samples', 'sample_13', 'connectivity', 'components'], [3] + [0] * 14), 1),
        ('same_rank_used_as_counterexample', altered(['counterexample', 'samples'], ['sample_07', 'sample_11']), 0),
        ('same_counts_but_weaker_agreement',
         altered(['counterexample'], {'samples': ['sample_01', 'sample_02'], 'agreement': 'concentration'}), 0),
        ('unsupported_stronger_claim', altered(['counterexample', 'agreement'], 'axis_profile'), 0),
        ('duplicate_pair', altered(['counterexample', 'samples'], ['sample_02', 'sample_02']), 0),
        ('unknown_id', altered(['counterexample', 'samples'], ['sample_02', 'sample_99']), 0),
        ('only_samples', {'samples': GOOD['samples']}, 0),
        ('only_counts', {'samples': {name: row['missing_site_count'] for name, row in GOOD['samples'].items()}}, 0),
    ])
    reports = run_cases(cases)
    if args.report:
        args.report.write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(reports)} CLI reward checks passed')
