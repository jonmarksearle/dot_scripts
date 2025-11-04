# Web Search Command

## Purpose
Perform web searches from newline-separated queries. Results contain the top links returned by the configured engines.

## Behaviour
- Consume `~/.codex.search.txt` (or stdin) for queries; skip blank lines.
- Attempt engines in order (currently Brave, then DuckDuckGo). If an engine fails or yields no results, move to the next.
- Parse the result HTML with engine-specific parsers, capturing up to 10 `http(s)` links and titles.
- Print for each successful query:
  - Header `Query: <original query> (engine: <engine name>)`
  - Numbered lines `1. Title — URL`
- Emit engine errors to stderr while continuing with later queries.
- Exit code is `0` when every query produced a result block; `1` when any query failed.

## Example
```bash
./search.py < ~/.codex.search.txt
```

Populate `~/.codex.search.txt` with newline-separated queries before running the command. In offline setups the command will report network errors but still exercise parsing and validation paths.

## Notes
- Engine sequence and parsers live in `search.py`; behaviour tests are under `tests/test_search.py`.
- Network access is required for real results; failures are surfaced but do not halt later queries.
