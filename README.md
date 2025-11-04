# Scripts

This directory hosts a collection of batch-friendly Python utility scripts.
Each script is designed to be standalone and includes its dependencies and Python version compatibility via PEP 723 metadata.

## Usage

To run a script, make it executable (`chmod +x <script_name.py>`) and then execute it directly. For example:

```bash
./search.py < ~/.codex.search.txt
./browse.py < ~/.codex.browse.txt
./flines.py <file_path>
```

Populate `~/.codex.search.txt` and `~/.codex.browse.txt` with newline-separated queries or URLs respectively.

## Development

Use the `justfile` for common development tasks:

*   **Format:** `just format` (uses `uvx ruff format`)
*   **Lint:** `just lint` (uses `uvx ruff check` and `uvx mypy`)
*   **Test:** `just test` (uses `PYTHONPATH=. uvx pytest`)

Expect network errors when the environment lacks external access; the scripts still exercise the pipeline.
