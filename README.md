# scripts

## Overview

scripts: `/home/jon/Work/.scripts/`

This directory hosts a collection of batch-friendly Python utility scripts.
Each script is designed to be standalone and includes its dependencies and Python version compatibility via PEP 723 metadata.

* `search.py`: Performs web searches from newline-separated queries.
* `browse.py`: Fetches and renders web pages as plain text.
* `flines.py`: Counts the number of lines in each Python function within a specified Python file.
* `mhtml2md.py`: Converts MHTML exports to Markdown with image extraction.
* `clean_md.py`: Cleans Confluence Markdown exports and removes boilerplate assets.
* `copyImage.py`: Saves the current clipboard image to a timestamped JPEG file and prints its path.

## Documentation

* `README.md`: Overview of the scripts and development commands.
* `browse.md`: Details the web browsing command.
* `search.md`: Outlines the web search command.
* `flines.md`: Documents the function line counter command.
* `mhtml2md.md`: Guides the MHTML conversion command.
* `clean_md.md`: Details the Markdown clean-up command.

## Usage

```bash
/home/jon/Work/.scripts/search.py < .codex.search.txt
/home/jon/Work/.scripts/browse.py < .codex.browse.txt
/home/jon/Work/.scripts/flines.py <file_path>
/home/jon/Work/.scripts/mhtml2md.py <mhtml_file>
/home/jon/Work/.scripts/clean_md.py <path_to_md_or_dir>
/home/jon/Work/.scripts/copyImage.py
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
