# Clean Markdown Exports

## Purpose

Clean Confluence Markdown exports by removing boilerplate navigation, trimming related content, and deleting known boilerplate assets.

## Behaviour

- Keeps the first title line.
- Keeps the first `[Updated ...](...)` line when present.
- Keeps the first `# ...` header and everything after it.
- Removes everything between the title line and the first `# ...` header.
- Drops any standalone `Add label` line.
- Replaces the `Related contentMore info` section with a cleaned list of related links:
  - `Name - [Title](URL)`
- Removes lines referencing known boilerplate assets.
- Deletes known boilerplate assets from the target directory (missing files are ignored).

## Usage

```bash
/home/jon/Work/.scripts/clean_md.py <path_to_md_or_dir>
```
