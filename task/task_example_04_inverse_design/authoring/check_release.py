"""Author-side exact allowlist validation; does not test actual network isolation."""
from pathlib import Path
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('--release-root', type=Path, required=True)
parser.add_argument('--manifest', type=Path, required=True)
args = parser.parse_args()
root = args.release_root.resolve()
spec = json.loads(args.manifest.read_text(encoding='utf-8'))
expected = spec['task_files']
found, links = {}, []
for path in root.rglob('*'):
    rel = path.relative_to(root).as_posix()
    if path.is_symlink():
        links.append(rel)
    if path.is_file():
        found[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
result = dict(missing=sorted(set(expected)-set(found)),unexpected=sorted(set(found)-set(expected)),
              altered=sorted(k for k in found.keys() & expected.keys() if found[k]!=expected[k]),symlinks=links)
result['passed'] = not any(result.values())
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
