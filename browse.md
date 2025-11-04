# Web Browse Command

## Purpose
Provide a single approved command for fetching and rendering web pages as plain text. Input is newline-separated URLs, output is the rendered text body for each URL.

## Behaviour
- Read `~/.codex.browse.txt` (or stdin) for URLs; ignore blank lines.
- Validate that each URL begins with `http://` or `https://`; report unsupported schemes.
- Use `urllib.request.urlopen` to download content with a timeout; report HTTP/network errors per URL.
- Render the payload through `lynx -dump -stdin` and print:
  - `URL: <original URL>` header
  - Plain-text body (adds a trailing newline when absent)
- Continue processing remaining URLs even if a previous URL fails.
- Exit code is `0` when all URLs succeed, `1` if any error was emitted.

## Example
```bash
uvx browse < ~/.codex.browse.txt
```

Populate `~/.codex.browse.txt` with newline-separated URLs before running the command. The tool writes a plain-text dump for each URL to stdout and errors to stderr.

## Notes
- `lynx` must be available on `PATH`; the command exits immediately when the dependency is missing.
- Network failures are expected in offline environments; the tool still exercises validation and logging.
- The implementation lives in `browse.py`; tests reside in `tests/test_browse.py`.
