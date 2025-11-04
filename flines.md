# Function Line Counter Command

## Purpose
Count the number of lines in each Python function within a specified Python file.

## Behaviour
- Takes a Python file path as an argument.
- Parses the file using Python's `ast` module.
- Identifies all functions (including async functions) and their start and end line numbers.
- Calculates the line count for each function.
- Presents the function name, line count, start line, and end line in a formatted table using `rich`.
- If no functions are found, it reports that no functions were found.
- Displays Python, Typer, and Rich versions in the footer.

## Example
```bash
./flines.py <file_path>
```

## Notes
- The script uses `typer` for command-line interface and `rich` for rich text formatting.
- It requires `typer` and `rich` to be installed, as specified in its PEP 723 metadata.
- The implementation lives in `flines.py`.
