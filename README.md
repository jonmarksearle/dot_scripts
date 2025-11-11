# Scripts

## Overview

Scripts: `/home/jon/Work/.Scripts/`

This directory hosts a collection of batch-friendly Python utility scripts.
Each script is designed to be standalone and includes its dependencies and Python version compatibility via PEP 723 metadata.

*   `search.py`: Performs web searches from newline-separated queries.
*   `browse.py`: Fetches and renders web pages as plain text.
*   `flines.py`: Counts the number of lines in each Python function within a specified Python file.

## Documentation

*   `README.md`: Overview of the scripts and development commands.
*   `browse.md`: Details the web browsing command.
*   `search.md`: Outlines the web search command.
*   `flines.md`: Documents the function line counter command.

## Usage

```bash
/home/jon/Work/.Scripts/search.py < .codex.search.txt
/home/jon/Work/.Scripts/browse.py < .codex.browse.txt
/home/jon/Work/.Scripts/flines.py <file_path>
```

Populate '.codex.search.txt' and '.codex.browse.txt` with newline-separated queries or URLs respectively.

```bash
cat << 'EOF' > .codex.search.txt
<queries>
EOF
cat << 'EOF' > .codex.browse.txt
<urls>
EOF
```
