"""Check submitted local controls against the independently enumerated windows."""
import argparse
import json
import math
from pathlib import Path

CONTEXT = json.loads(Path(__file__).with_name('condition_context.json').read_text(encoding='utf-8'))


def check_comparison(submitted, targets):
    if not isinstance(submitted, dict) or submitted.keys() != targets.keys():
        raise ValueError('Expected all eleven film condition IDs')
    for name, choices in targets.items():
        row = submitted[name]
        if not isinstance(row, dict):
            raise ValueError(f'{name}: expected a comparison object')
        if len(choices[0]) == 1:
            if row != choices[0]:
                raise ValueError(f'{name}: incorrect support or unresolved status')
            continue
        if set(row) != {'status', 'controls', 'margin_dex'}:
            raise ValueError(f'{name}: directional comparison requires controls and margin')
        margin = row['margin_dex']
        if type(margin) not in (int, float) or not math.isfinite(margin) or margin <= .30:
            raise ValueError(f'{name}: margin must be finite and greater than 0.30 dex')
        for target in choices:
            if (row['status'] == target['status'] and row['controls'] == target['controls']
                    and abs(margin - target['margin_dex']) <= .02 + 1e-12):
                break
        else:
            raise ValueError(f'{name}: unsupported direction, control window or margin')


def check_sections(payload, record):
    if not isinstance(payload, dict):
        raise ValueError('Answer must be an object')
    if set(payload) - set(CONTEXT) - {'analysis'}:
        raise ValueError('Unexpected answer fields')
    for name, targets in CONTEXT.items():
        record(name, lambda: check_comparison(payload[name], targets))

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
