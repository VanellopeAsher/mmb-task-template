"""Exact release allowlist + UTF-8 fingerprint; accepts CRLF/LF only."""
from pathlib import Path
import argparse
import json
from release_hash import content_sha256, validate_policy

parser=argparse.ArgumentParser()
parser.add_argument('--release-root',type=Path,required=True)
parser.add_argument('--manifest',type=Path,required=True)
args=parser.parse_args()
root=args.release_root.resolve()
spec=json.loads(args.manifest.read_text(encoding='utf-8'))
validate_policy(spec)
expected=spec['task_files']
found,links,invalid_encoding={},{},[]
for path in root.rglob('*'):
    rel=path.relative_to(root).as_posix()
    if path.is_symlink():
        links[rel]=True
    if path.is_file():
        try:
            found[rel]=content_sha256(path)
        except UnicodeDecodeError:
            invalid_encoding.append(rel)
            found[rel]=None
result=dict(missing=sorted(set(expected)-set(found)),unexpected=sorted(set(found)-set(expected)),
            altered=sorted(k for k in found.keys() & expected.keys() if found[k]!=expected[k]),
            symlinks=sorted(links),invalid_encoding=invalid_encoding)
result['passed']=not any(result.values())
result['hash_policy']=spec['hash_policy']
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
