"""Find local controls from the public measurements without fitting a response curve."""
import argparse
import csv
import json
import math
from pathlib import Path


def assess_window(film, controls, axis, half_width):
    x, y = film[axis], film['c2plus']
    left = [row for row in controls if row[axis] + half_width <= x - half_width]
    right = [row for row in controls if row[axis] - half_width >= x + half_width]
    if not left or not right:
        return {'status': 'outside_support'}

    # Every other eligible window contains this one. Its envelope gives the
    # best chance of separating the film from the controls in either direction.
    lower = max(left, key=lambda row: row[axis])
    upper = min(right, key=lambda row: row[axis])
    possible = [row['c2plus'] for row in controls
                if row[axis] + half_width >= lower[axis] - half_width
                and row[axis] - half_width <= upper[axis] + half_width]
    margins = {'higher': y - max(possible) - .16, 'lower': min(possible) - y - .16}
    for status, margin in margins.items():
        if margin > .30:
            return {'status': status, 'controls': [lower['id'], upper['id']], 'margin_dex': margin}
    return {'status': 'unresolved'}



def generate(data_dir):
    with (data_dir / 'observations.csv').open(encoding='utf-8', newline='') as stream:
        rows = [
            dict(id=row['condition_id'], composition=row['composition'], additive=row['additive'],
                 currents={key: float(row[key]) for key in (
                     "j_CH4_mA_cm2", "j_C2plus_mA_cm2")},
                 methane=math.log10(float(row['j_CH4_mA_cm2'])),
                 c2plus=math.log10(float(row['j_C2plus_mA_cm2'])),
                 potential=float(row['potential_V_RHE']))
            for row in csv.DictReader(stream)
        ]
    bare = [row for row in rows if row['additive'] == 'none']
    findings = {}
    for film in rows:
        if film['additive'] == 'none':
            continue
        matched = [row for row in bare if row['composition'] == film['composition']]
        status = assess_window(film, matched, 'methane', .08)['status']
        finding = {'status': status}
        if status in ('higher', 'lower'):
            finding.update(film['currents'])
        else:
            finding['status'] = 'insufficient_evidence'
        findings[film['id']] = finding
    return {'findings': findings}



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('/workspace/data'))
    parser.add_argument('--output', type=Path, default=Path('/workspace/results/answer.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(args.data_dir), indent=2) + '\n', encoding='utf-8', newline='\n')
