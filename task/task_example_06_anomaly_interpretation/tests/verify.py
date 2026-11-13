"""Check defect, repeat and connectivity claims against independent CIF reconstruction."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = json.loads((HERE / 'reference_answer.json').read_text(encoding='utf-8'))['samples']
AXES = json.loads((HERE / 'axis_reference.json').read_text(encoding='utf-8'))
CONTROL = json.loads((HERE / 'control_reference.json').read_text(encoding='utf-8'))


def check_spatial(row, expected, missing):
    if not isinstance(row, dict):
        raise ValueError('Expected spatial evidence object')
    if set(row) == {'full_repeat_axes'}:
        count = row['full_repeat_axes']
        if type(count) is int and count == expected.count(missing):
            return
    elif set(row) == {'overlap_counts'}:
        counts = row['overlap_counts']
        if isinstance(counts, list) and all(type(v) is int for v in counts) and sorted(counts) == expected:
            return
    raise ValueError('Incorrect repeat evidence')


def check_connectivity(row, expected, axes):
    if not isinstance(row, dict) or set(row) != {'method', 'components'}:
        raise ValueError('Expected connectivity method and components')
    parts = row['components']
    if row['method'] == 'winding_rank':
        if isinstance(parts, list) and all(type(v) is int for v in parts) and sorted(parts) == expected:
            return
    elif row['method'] == 'axis_spans':
        if (isinstance(parts, list) and all(isinstance(part, list) and len(part) == 3
                                            and all(type(v) is bool for v in part) for part in parts)
                and sorted(parts) == axes and sorted(map(sum, parts)) == expected):
            return
    raise ValueError('Connectivity evidence does not establish all component ranks')


def check_sections(payload, record):
    if not isinstance(payload, dict) or set(payload) - {'samples', 'counterexample', 'analysis'}:
        raise ValueError('Invalid answer fields')
    samples = payload['samples']
    if not isinstance(samples, dict) or samples.keys() != REFERENCE.keys():
        raise ValueError('Samples must cover the reference panel')
    for name, row in samples.items():
        if not isinstance(row, dict) or row.keys() != REFERENCE[name].keys():
            raise ValueError(f'{name}: incorrect sample fields')

    def defects():
        for name, row in samples.items():
            expected = REFERENCE[name]
            if (row['defect_type'] != expected['defect_type'] or type(row['missing_site_count']) is not int
                    or row['missing_site_count'] != expected['missing_site_count']):
                raise ValueError(f'{name}: incorrect vacancy assignment or count')

    def repeats():
        for name, row in samples.items():
            expected = REFERENCE[name]
            check_spatial(row['spatial'], expected['spatial']['overlap_counts'], expected['missing_site_count'])

    def connectivity():
        for name, row in samples.items():
            expected = REFERENCE[name]
            check_connectivity(row['connectivity'], expected['connectivity']['components'], AXES[name])
            if row['network_status'] != expected['network_status']:
                raise ValueError(f'{name}: incorrect 3D coverage conclusion')

    def contrast():
        row = payload['counterexample']
        if not isinstance(row, dict) or set(row) != {'samples', 'agreement'}:
            raise ValueError('Expected one pair and its summary agreement level')
        pair = row['samples']
        if (not isinstance(pair, list) or len(pair) != 2 or any(type(name) is not str for name in pair)
                or pair[0] == pair[1]):
            raise ValueError('Expected two different sample IDs')
        if row['agreement'] != CONTROL['agreement'] or sorted(pair) not in CONTROL['samples']:
            raise ValueError('Pair does not establish the strongest summary match with different periodic ranks')

    record('defect_identification', defects)
    record('spatial_repetition', repeats)
    record('periodic_connectivity', connectivity)
    record('counterexample_selection', contrast)

CHECK_ERRORS = (ValueError, KeyError, TypeError, OverflowError, RecursionError, IndexError)


def assess(payload):
    sections = {}

    def record(name, check):
        try:
            check()
            sections[name] = {'passed': True}
        except CHECK_ERRORS as exc:
            sections[name] = {'passed': False, 'reason': str(exc)}

    try:
        check_sections(payload, record)
    except CHECK_ERRORS as exc:
        sections['format'] = {'passed': False, 'reason': str(exc)}
    return sections


def verify(payload):
    sections = assess(payload)
    failures = [f"{name}: {result['reason']}" for name, result in sections.items() if not result['passed']]
    if failures:
        raise ValueError('; '.join(failures))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--answer', default='/workspace/results/answer.json')
    parser.add_argument('--reward', default='/logs/verifier/reward.txt')
    args = parser.parse_args()
    try:
        sections = assess(json.loads(Path(args.answer).read_text(encoding='utf-8')))
    except (OSError, ValueError, RecursionError) as exc:
        sections = {'format': {'passed': False, 'reason': str(exc)}}
    ok = bool(sections) and all(section['passed'] for section in sections.values())
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text('1\n' if ok else '0\n', encoding='utf-8')
    reward.with_name('assessment.json').write_text(
        json.dumps({'reward': int(ok), 'sections': sections}, indent=2) + '\n', encoding='utf-8')
    print('PASS' if ok else 'FAIL')


if __name__ == '__main__':
    main()
