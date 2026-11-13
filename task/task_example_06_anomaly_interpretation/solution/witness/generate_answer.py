"""Diagnose periodic connectivity and select a control from the public CIFs."""
import argparse
from itertools import combinations
import json
from pathlib import Path

from structure_metrics import inspect_cif


def agreement(a, b):
    if (a['defect_type'], a['missing_site_count']) != (b['defect_type'], b['missing_site_count']):
        return 0
    if a['nearest_missing_pairs'] != b['nearest_missing_pairs']:
        return 1
    if sum(a['overlap_counts']) != sum(b['overlap_counts']):
        return 2
    return 4 if a['overlap_counts'] == b['overlap_counts'] else 3


def generate(data_dir):
    metrics = {path.stem: inspect_cif(path, data_dir / 'reference.cif')
               for path in sorted((data_dir / 'structures').glob('sample_*.cif'))}
    samples = {}
    for name, row in metrics.items():
        ranks = row['component_winding_ranks']
        status = 'no_3d_network'
        if 3 in ranks:
            status = 'single_3d_network' if len(ranks) == 1 else 'partial_3d_network'
        samples[name] = dict(defect_type=row['defect_type'], missing_site_count=row['missing_site_count'],
                             spatial={'overlap_counts': row['overlap_counts']},
                             connectivity={'method': 'winding_rank', 'components': ranks},
                             network_status=status)
    candidates = [(agreement(metrics[a], metrics[b]), a, b) for a, b in combinations(metrics, 2)
                  if max(metrics[a]['component_winding_ranks']) != max(metrics[b]['component_winding_ranks'])]
    score, left, right = max(candidates)
    if not score:
        raise ValueError('No concentration-matched periodic contrast')
    grades = ('concentration', 'nearest_pairs', 'mean_repeat', 'axis_profile')
    return {'samples': samples, 'counterexample': {'samples': [left, right], 'agreement': grades[score - 1]}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('/workspace/data'))
    parser.add_argument('--output', type=Path, default=Path('/workspace/results/answer.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(args.data_dir), indent=2) + '\n', encoding='utf-8', newline='\n')
