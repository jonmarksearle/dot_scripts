# Review of `.scripts/clean_md.py`

## Critical Findings

### 1. Aggressive Non-ASCII Cleaning
**Severity:** High
**Location:** `_clean_non_ascii`

The function uses `re.sub(r"[^\x00-\x7F]+", " ", line)` which strips **all** non-ASCII characters.
- **Impact:** This destroys international text, emojis, mathematical symbols, and smart punctuation (like curly quotes or en-dashes) that are valid in Markdown.
- **Recommendation:** Replace with Unicode normalization (e.g., `unicodedata.normalize`) or specific replacement maps (e.g., smart quotes to ASCII quotes) if strictly necessary. In 2026, Markdown files should generally support UTF-8.

### 2. Unsafe File Deletion
**Severity:** High
**Location:** `remove_asset_files`

The script automatically deletes files matching `_ASSET_SUFFIXES` in the target directory.
- **Impact:** Data loss. There is no confirmation prompt, no dry-run option, and the list of suffixes includes generic terms like `favicon.ico` or specific user images that might be legitimate in other contexts.
- **Recommendation:** Add a `--dry-run` flag. Do not delete files by default without explicit user confirmation (`--force` or interactive prompt).

## Maintainability & Fragility

### 1. Hardcoded Asset List
**Location:** `_ASSET_SUFFIXES`
The list contains specific filenames (e.g., "Jon Searle.webp", "89278e2b1046.png"). This makes the script brittle and specific to one user's export history.
- **Recommendation:** Move these to a configuration file or use regex patterns to identify generated asset filenames.

### 2. Specific Confluence Strings
**Location:** `_split_related`, `_is_add_label`
The script relies on exact string matches like "Related contentMore info" and "Add label".
- **Impact:** If Atlassian changes the export format slightly (e.g., "Related Content"), the script will break or fail to clean the footer.

### 3. Header Extraction Logic
**Location:** `_strip_to_header`
The script assumes a structure of `Title -> Metadata -> # Header`.
- **Impact:** Documents that don't match this exact structure (e.g., missing the H1 or having content before it) might have their introductory text incorrectly stripped.

## Code Style

- **Type Hinting:** Good use of `Path | None` and `Iterator`.
- **Modularity:** Functions are small and focused, which is good.

## Summary of Recommendations

1.  **Stop stripping Unicode:** Remove `_clean_non_ascii` or make it an optional flag for specific legacy systems.
2.  **Safety First:** Disable `remove_asset_files` by default or wrap it in a `confirm` dialog/dry-run check.
3.  **Generalize Patterns:** Replace hardcoded filenames with patterns where possible.
