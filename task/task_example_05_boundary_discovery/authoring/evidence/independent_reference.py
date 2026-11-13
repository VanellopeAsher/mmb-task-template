"""Derive the complete local-window acceptance set independently of the Oracle."""
import csv
from itertools import combinations
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
COMPARISONS = {
    'matched_methane': ('j_CH4_mA_cm2', .16, True),
    'pooled_methane': ('j_CH4_mA_cm2', .16, False),
    'matched_potential': ('potential_V_RHE', .030, True),
}


def acceptance(rows, film, column, separation, matched, reading_half_width=.08, threshold=.30):
    controls = [r for r in rows if r['additive'] == 'none'
                and (not matched or r['composition'] == film['composition'])]
    convert = float if column == 'potential_V_RHE' else lambda value: np.log10(float(value))
    controls.sort(key=lambda r: convert(r[column]))
    x = np.array([convert(r[column]) for r in controls])
    y = np.log10([float(r['j_C2plus_mA_cm2']) for r in controls])
    tx = convert(film[column])
    ty = np.log10(float(film['j_C2plus_mA_cm2']))
    brackets = []
    for left, right in combinations(range(len(controls)), 2):
        if min(tx - x[left], x[right] - tx) < separation:
            continue
        include = (x >= x[left] - separation) & (x <= x[right] + separation)
        lo, hi = np.min(y[include]) - reading_half_width, np.max(y[include]) + reading_half_width
        if ty - reading_half_width > hi + threshold:
            status, margin = 'higher', ty - reading_half_width - hi
        elif ty + reading_half_width < lo - threshold:
            status, margin = 'lower', lo - (ty + reading_half_width)
        else:
            status, margin = 'unresolved', None
        brackets.append(dict(status=status, controls=[controls[i]['condition_id'] for i in (left, right)],
                             margin_dex=None if margin is None else float(margin)))
    directional = [row for row in brackets if row['margin_dex'] is not None]
    if directional:
        return directional
    return [{'status': 'unresolved' if brackets else 'outside_support'}]


def save(path, payload):
    (ROOT / path).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    with (ROOT / 'environment/data/observations.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    catalog = {
        name: {film['condition_id']: acceptance(rows, film, *params) for film in rows if film['additive'] != 'none'}
        for name, params in COMPARISONS.items()
    }
    # The reference demonstrates a maximizing window. The alternative uses the
    # first qualifying interval in sorted control order, without optimizing the gap.
    reference = {key: {name: max(choices, key=lambda row: row.get('margin_dex', 0))
                       for name, choices in group.items()} for key, group in catalog.items()}
    alternative = {key: {name: choices[0] for name, choices in group.items()} for key, group in catalog.items()}
    save('authoring/evidence/reference_answer.json', reference)
    save('authoring/evidence/alternative_answer.json', alternative)
    save('tests/reference_answer.json', reference)
    save('tests/condition_context.json', catalog)
    scenarios = {}
    for width, threshold in ((.04, .30), (.08, .30), (.12, .30), (.08, .25), (.08, .35)):
        reports = {}
        for key, (column, _, matched) in COMPARISONS.items():
            separation = .030 if column == 'potential_V_RHE' else 2 * width
            reports[key] = {film['condition_id']: acceptance(rows, film, column, separation, matched, width, threshold)[0]['status']
                            for film in rows if film['additive'] != 'none'}
        scenarios[f'reading_{width:.2f}_effect_{threshold:.2f}_dex'] = reports
    leave_one_out = {}
    for bare in (row for row in rows if row['additive'] == 'none'):
        subset = [row for row in rows if row != bare]
        leave_one_out[bare['condition_id']] = {
            key: {film['condition_id']: acceptance(subset, film, *params)[0]['status']
                  for film in rows if film['additive'] != 'none'}
            for key, params in COMPARISONS.items()
        }
    save('authoring/evidence/sensitivity.json', dict(scenarios=scenarios, leave_one_control_out=leave_one_out))
    print({key: {name: row['status'] for name, row in group.items()} for key, group in reference.items()})
