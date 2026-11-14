"""Check submitted local controls against the independently enumerated windows."""
import argparse
import json
import math
from pathlib import Path

REFERENCE = json.loads(Path(__file__).with_name('reference_answer.json').read_text(encoding='utf-8'))


def check_findings(findings):
    reference = REFERENCE['findings']
    if not isinstance(findings, dict) or not findings or set(findings) - set(reference):
        raise ValueError('Use existing additive observation IDs')
    directional = limited = False
    for name, row in findings.items():
        if not isinstance(row, dict):
            raise ValueError(f'{name}: expected a finding object')
        status = row.get('status')
        supported_status = reference[name]['status']
        if status in ('higher', 'lower'):
            if status != supported_status or set(row) != {
                'status', 'j_CH4_mA_cm2', 'j_C2plus_mA_cm2'
            }:
                raise ValueError(f'{name}: unsupported direction or missing observed currents')
            for column in ('j_CH4_mA_cm2', 'j_C2plus_mA_cm2'):
                expected = reference[name][column]
                value = row[column]
                if (type(value) not in (int, float) or not math.isfinite(value) or value <= 0
                        or abs(math.log10(value) - math.log10(expected)) > .08 + 1e-12):
                    raise ValueError(f'{name}: incorrect {column}')
            directional = True
        elif status == 'insufficient_evidence':
            if supported_status in ('higher', 'lower') or set(row) != {'status'}:
                raise ValueError(f'{name}: incorrect evidence limitation')
            limited = True
        else:
            raise ValueError(f'{name}: unknown status')
    if not directional or not limited:
        raise ValueError('Report both a supported deviation and an evidence limitation')


def check_sections(payload, record):
    if not isinstance(payload, dict) or set(payload) - {'findings', 'analysis'}:
        raise ValueError('Expected findings and optional analysis')
    record('findings', lambda: check_findings(payload['findings']))


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
