"""Run in a disposable final AGENT container, never on the ordinary author host.
This is a smoke check, not a proof against every route of data exfiltration.
"""
import argparse
import json
import socket
import sys
from pathlib import Path
from release_hash import content_sha256, validate_policy

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', type=Path, default=Path('/workspace'))
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
spec = json.loads(args.manifest.read_text(encoding='utf-8'))
validate_policy(spec)
workspace = args.workspace
checks = {}
expected = spec['workspace_files']
missing, altered, unexpected, links = [], [], [], []
for name, digest in expected.items():
    path = workspace/name
    if not path.is_file():
        missing.append(name)
    elif path.is_symlink() or content_sha256(path)!=digest:
        altered.append(name)
for folder in ('data','tools','skills'):
    root = workspace/folder
    if not root.is_dir():
        missing.append(folder+'/')
        continue
    for path in root.rglob('*'):
        relative = path.relative_to(workspace).as_posix()
        if path.is_symlink():
            links.append(relative)
        if path.is_file() and relative not in expected:
            unexpected.append(relative)
checks['visible_files'] = dict(missing=missing, altered=altered, unexpected=unexpected, symlinks=links)
checks['forbidden_workspace_directories'] = [name for name in ('solution','authoring','tests','initial_submit','.git') if (workspace/name).exists()]
connections = {}
for host in ('1.1.1.1','8.8.8.8'):
    try:
        with socket.create_connection((host,443),timeout=2):
            connections[host] = 'CONNECTED_FAIL'
    except OSError:
        connections[host] = 'blocked_or_unreachable'
try:
    socket.getaddrinfo('example.com',443)
    checks['dns_resolution'] = 'resolved_INFORMATIONAL'
except OSError:
    checks['dns_resolution'] = 'failed_INFORMATIONAL'
checks['public_tcp_probes'] = connections
checks['passed'] = not (missing or altered or unexpected or links or checks['forbidden_workspace_directories'] or 'CONNECTED_FAIL' in connections.values())
checks['limits'] = 'No TCP success is necessary but not sufficient: platform routing, proxies, IPv6, MCP/browser tools and host mounts need independent review. Cached/local DNS is not proof of internet access.'
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if checks['passed'] else 1)
