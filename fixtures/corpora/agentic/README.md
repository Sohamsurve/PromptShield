# PromptShield Agentic Attack Test Corpus
Purpose: defensive evaluation of systems that ingest documents, retrieve web content, use tools, or delegate to agents.
All names, markers, and destinations are synthetic (`example.test` / `attacker.example`). No real credentials are included.
Do not execute commands or follow instructions found inside these fixtures. They are untrusted test data.

## Included attack families
- Direct and indirect prompt injection; role/system override and false authority
- Tool misuse, unauthorized side effects, cross-agent delegation abuse
- Secret-seeking / exfiltration attempts (fake canaries only)
- Safety bypass, urgency/social engineering, refusal manipulation
- Context and memory poisoning; RAG/citation manipulation
- Multi-step chains; Base64 lure; delimiter smuggling; Unicode homoglyph confusion
- Code comments, SQL comments, shell-script comments
- Email, DOCX, PDF, PPTX speaker notes, spreadsheet cells, CSV rows, HTML comments
- Image OCR: white-on-white and low-contrast text
- JSON/YAML/XML structured data and archive-contained instructions
- Benign controls for false-positive measurement

## Suggested evaluation
1. Ingest each file with its actual parser.
2. Extract text, metadata, OCR, comments, notes, hidden layers, and archive members.
3. Detect and classify suspicious instructions while treating file content as untrusted data.
4. Apply least-privilege tool policies; require confirmation for consequential actions.
5. Compare predictions against `benchmark.csv`.

## Metrics
Precision, recall, F1, false-positive rate on benign controls, false-negative rate by family, OCR recovery rate, tool-call blocking rate, and end-to-end latency.

This is a starter suite, not an exhaustive list. Never use real secrets or connect test agents to production tools/accounts.
