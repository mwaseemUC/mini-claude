| System | Model | Passed | Needs execution | Ordinary | Avg LLM calls | Avg tool calls | Cost/task | Total cost | p50 latency |
|---|---|---|---|---|---|---|---|---|---|
| agent | claude-haiku-5-5 | 10/10 | 4/4 | 6/6 | 4.7 | 6.9 | $0.0014 | $0.0139 | 9.5s |
| agent | claude-sonnet-5-5 | 10/10 | 4/4 | 6/6 | 4.1 | 5.4 | $0.0176 | $0.1755 | 9.2s |
| single-shot | claude-haiku-5-5 | 8/10 | 2/4 | 6/6 | 1.0 | 0.0 | $0.0008 | $0.0077 | 6.0s |
| single-shot | claude-sonnet-5-5 | 8/10 | 2/4 | 6/6 | 1.0 | 0.0 | $0.0084 | $0.0837 | 4.8s |

| Task | agent / claude-haiku-5-5 | agent / claude-sonnet-5-5 | single-shot / claude-haiku-5-5 | single-shot / claude-sonnet-5-5 |
|---|---|---|---|---|
| t01-slugify | pass | pass | pass | pass |
| t02-paginate-offbyone | pass | pass | pass | pass |
| t03-wordcount-cli | pass | pass | pass | pass |
| t04-lru-cache | pass | pass | pass | pass |
| t05-rename-api | pass | pass | pass | pass |
| t06-invoice-totals | pass | pass | pass | pass |
| t07-manifest-hashes | pass | pass | fail | fail |
| t08-vendor-pyc | pass | pass | fail | fail |
| t09-cp1252-csv | pass | pass | pass | pass |
| t10-test-pollution | pass | pass | pass | pass |
