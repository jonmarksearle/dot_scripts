# Clipboard Image Command

## Purpose

Capture the current clipboard image and persist it as a timestamped JPEG file, printing the saved path so downstream tools can reference it.

## Behaviour

- Attempts clipboard backends in order (`wl-paste`, `xclip`, then `pngpaste`). The first backend that returns image bytes wins; missing binaries are skipped with a note in stderr.
- Accepts no arguments; optionally set the working directory to choose the output location.
- Converts the clipboard image to JPEG, writes `.temp_<UTC timestamp>_<hash>.jpg` into the current (or provided) directory, and prints the absolute path to stdout.
- Emits errors to stderr when the clipboard is empty, lacks an image, or no supported backend is available.
- Exit code is `0` when the image is saved, `1` when the command fails.

## Example

```bash
./copyImage.py
```

Place the image you want on the clipboard, run the script, and it will report the saved file path for further processing.

## Notes

- Requires at least one clipboard utility (`wl-paste`, `xclip`, or `pngpaste`) plus JPEG support via Pillow (declared in the script metadata).
- Files are written to the current directory unless `output_dir` is provided via embedding the script in another tool.
- Tests live under `tests/test_copyImage.py` and cover success/failure flows.
