# MHTML to Markdown Converter

## Purpose

Convert Confluence .mhtml exports into a clean Markdown file with extracted and linked images.

## Behaviour

- Accepts an input `.mhtml` file path (must exist and be readable).
- Optionally accepts an output directory via `--outdir` (defaults to the input file's parent directory).
- Parses the MHTML structure to separate HTML content from binary image attachments.
- Performs intelligent image extraction:
  - Derives meaningful filenames from metadata (Content-ID, Content-Location, headers).
  - Automatically disambiguates duplicate filenames (e.g., `image (1).png`).
  - Writes extracted images to the target directory.
- Processes the HTML content:
  - Replaces `<img>` tags with local placeholders (e.g., `{image_name.png}`).
  - Converts HTML structure to standard Markdown using `markdownify`.
  - Normalizes whitespace and line breaks.
- Writes the final `.md` file to the target directory.
- Reports the path of the written Markdown file and a list of all extracted images to stdout.

## Example

```bash
./mhtml2md.py export.mhtml
./mhtml2md.py export.mhtml --outdir ./converted_docs
```

## Notes

- Designed specifically for Confluence MHTML exports but may work with other standard MHTML sources.
- Dependencies (`typer`, `beautifulsoup4`, `markdownify`, `lxml`) are managed via PEP 723 script metadata.
- Implementation lives in `mhtml2md.py`.
