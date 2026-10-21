"""Freeze and immediately verify E3-S0 artifact bytes; no external actions."""
import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parents[1]
paths=sorted(p for p in r.rglob('*') if p.is_file() and p.name!='artifact_integrity.json' and '__pycache__' not in p.parts and not p.name.startswith('._'))
hashes={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(r/'artifact_integrity.json').write_text(json.dumps(hashes,indent=2,ensure_ascii=False))
assert all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in hashes.items())
print('Final artifact integrity PASS',len(hashes),'files')
