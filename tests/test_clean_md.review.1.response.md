# Response: test_clean_md.py review n=1

Accepted
- Reordered failure tests to the top of the file.
- Renamed the mislabelled success test to `test__clean_md_text__success__uses_title_when_header_missing`.

Pushback
- None.

Changes implemented
- Moved `test__clean_md_text__fail__missing_title` and `test__clean__fail__no_md_files` above success cases.
- Renamed the missing-header test to reflect success behaviour.
