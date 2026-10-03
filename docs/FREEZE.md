# Freeze — v0.1-phase5

Git tag: `v0.1-phase5` · commit `68688ad75bfc5d82aabb22337c340bbe8839ebda` (evidence pack `07a6063` + fresh-clone doc fix)

SHA-256 digests of protected evaluation artefacts at tag `v0.1-phase5`.

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `docs/freeze/test_split.jsonl` (all `split=test` rows from `eval/data/**/*.jsonl` at freeze) | `cc846c3e875740a963946022e8a6c1c6c223f9f41047e134ccab5d7a3a571dc2` | 15336 |

## How to verify

```bash
shasum -a 256 eval/thresholds.yml
# rebuild freeze blob:
python3 -c "
import json, hashlib
from pathlib import Path
rows=[]
for p in sorted(Path('eval/data').rglob('*.jsonl')):
  for line in p.read_text().splitlines():
    if not line.strip(): continue
    r=json.loads(line)
    if r.get('split')=='test':
      rows.append(json.dumps(r, sort_keys=True, ensure_ascii=False))
Path('docs/freeze/test_split.jsonl').write_text('\\n'.join(rows)+'\\n')
print(hashlib.sha256(Path('docs/freeze/test_split.jsonl').read_bytes()).hexdigest())
"
```

## Adaptive first-run

First-run numbers for `eval/data/adaptive/round1.jsonl` are recorded in `docs/EVIDENCE.md` §7 **before** any detector changes (`detectors_changed: false`).
