"""Trusted author-side fingerprint; normalize CRLF only, not substantive text."""
import hashlib

HASH_POLICY = 'sha256-utf8-crlf-to-lf-v1'

def content_sha256(path):
    raw = path.read_bytes()
    raw.decode('utf-8', errors='strict')
    # Spaces, numbers, BOM, bare CR and final newlines remain significant.
    # JSON is never parsed or re-serialized for hashing.
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()

def validate_policy(spec):
    if spec.get('manifest_version') != 2 or spec.get('hash_policy') != HASH_POLICY:
        raise ValueError('Unsupported release manifest: install updated scripts AND version-2 manifest')
