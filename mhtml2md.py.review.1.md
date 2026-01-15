# Review of `.scripts/mhtml2md.py`

## Critical Findings

### 1. URL Fragment Handling in Filenames
**Severity:** High
**Location:** `_tail` and `_filename_from_headers` functions.

The script currently strips query parameters (`?`) from `Content-Location` headers but fails to strip URL fragments (`#`). This results in filenames containing long, messy strings like `filename.ext#media-blob-url=true&id=...`, which can cause filesystem issues and looks untidy.

**Evidence:**
```python
def _tail(content_location: str | None) -> str:
    if not content_location:
        return ""
    return content_location.split("/")[-1].split("?")[0]  # Missing .split("#")[0]
```

**Recommendation:**
Modify both `_tail` and `_filename_from_headers` to split on `#` as well.

### 2. Header Filename Parsing
**Severity:** Medium
**Location:** `_filename_from_headers`

Similar to the above, when falling back to `Content-Location` for a filename, the fragment is not removed.

## Code Quality & Improvements

### 1. `_safe_stem` Robustness
The regex in `_safe_stem` (`r"[\/\\:\*\?\"<>\|]+"`) covers standard filesystem reserved characters. However, it does not explicitly handle `#` (often used in fragments) or `%` (URL encoding). While fixing the extraction logic (`_tail`) is the root fix, making `_safe_stem` more aggressive wouldn't hurt.

### 2. Modern Python Usage
The script correctly uses PEP 723 metadata and Python 3.12+ type hinting syntax. This is good.

## Summary of Required Changes

1.  **Update `_tail`**:
    ```python
    def _tail(content_location: str | None) -> str:
        if not content_location:
            return ""
        # Split on ? then #
        return content_location.split("/")[-1].split("?")[0].split("#")[0]
    ```

2.  **Update `_filename_from_headers`**:
    Apply the same split logic to the fallback extraction to ensure consistency.
