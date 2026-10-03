# Freeze — v0.2-evidence

Git tag: `v0.2-evidence`.

SHA-256 digests of protected / evidence artefacts **before any further tuning**.

| Path | SHA-256 | Bytes |
|---|---|---:|
| `eval/thresholds.yml` | `b318a50630d10367538efe32dea9618952c122018fef45f3d4556c03656c2446` | 449 |
| `docs/freeze/test_split.jsonl` (all `split=test` **and** `adaptive-round-2` rows from `eval/data/**/*.jsonl`) | `36276a75680d890b2902a7a96b8287283c94a4c56c033664d91b2c462943658b` | 230678 |
| `models/calibration.json` | `92d52ce20c7131310e7f4111199c2815bf247de16720c283b374d91f4d71ba32` | 80016 |
| `eval/reports/leakage.json` | `cea167550bb7f922d3d0bd62e335b97a4693a53fafa83db06da3f22da0ea7439` | 2544 |
| `eval/reports/evidence.json` | `930c51379a0d189defef201e12601869194621f224ca707283d1e2210195b214` | 23169 |

## Policy at freeze

- Tune on: `train`, `dev` (adaptive round 1 **spent**)
- Never tune on: `test`, `adaptive-round-2`
- Classifier: `tfidf_logreg` only; no ONNX artifact
- Support threshold: heatmap cells need `n ≥ 22`

## How to verify

```bash
shasum -a 256 eval/thresholds.yml models/calibration.json eval/reports/leakage.json eval/reports/evidence.json
python3 -c "
import json, hashlib
from pathlib import Path
rows=[]
for p in sorted(Path('eval/data').rglob('*.jsonl')):
  for line in p.read_text().splitlines():
    if not line.strip(): continue
    r=json.loads(line)
    if r.get('split') in {'test','adaptive-round-2'}:
      rows.append(json.dumps(r, sort_keys=True, ensure_ascii=False))
Path('docs/freeze/test_split.jsonl').write_text('\\n'.join(rows)+'\\n')
print(hashlib.sha256(Path('docs/freeze/test_split.jsonl').read_bytes()).hexdigest())
"
```

## Prior freeze

`v0.1-phase5` remains the Phase-5 code freeze; this tag strengthens evidence only.
