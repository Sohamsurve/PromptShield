# Limitations (current)

## Length / fusion

- Unmatched `dev_redteam` is length-confounded (threshold acc 0.924). Claimed fit uses length-matched C: ACTED **0.533**, FPR **0.116** (≤2% NOT MET).
- Classifier has no explicit length feature; len↔score pearson **−0.485** on the C slice.

## Judge

- Dev-only eval (n=119). Independent sealed **not evaluated**.
- Sol acc 1.000 on this gray-zone set may not transfer; mini manip **0.446**.
- Offline judge-action path: FPR **0.200**, localise **0.463**.
- 5 s timeout can yield unknown under load (none observed on Sol in this run).

## Claims

- F/D on independent sealed: **not evaluated**.
- Aria LLM agent: **not evaluated**.
