# Test Review: test_clean_md.py (n=1)

Findings (highest severity first)

1) Failure tests are not ordered before success tests.
   - `test__clean_md_text__fail__missing_title` appears after many success tests.
   - Standards require failure tests first within the file.

2) Test naming mismatch: `test__clean_md_text__fail__missing_header` is a success path.
   - It asserts a normal transformation instead of an exception.
   - Rename to `...__success` or change it to a failure test (with `pytest.raises`) if failure is intended.

Notes
- Other tests look within the ≤5 executable line rule due to `_assert_clean` usage.
- Related-content behaviour seems consistent with current implementation.
