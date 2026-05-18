"""
Extract every supported file in testing_files/ and print the API-style response.

Add samples to: testing_files/
Run:           pytest test_testing_files.py -s
Manual:        python run_local_extract.py
"""
import json

import pytest

from run_local_extract import TESTING_FILES_DIR, extract_local_file, list_testing_files

TESTING_FILES = list_testing_files()


def _assert_greenberg_template(content: str) -> None:
    assert "AC Analytical Controls" in content
    assert "Frendz Finance" in content


@pytest.mark.skipif(not TESTING_FILES_DIR.is_dir(), reason="testing_files/ directory missing")
def test_testing_files_directory_has_samples():
    assert TESTING_FILES, (
        f"Add supported files to {TESTING_FILES_DIR} "
        "(.pdf, .docx, .doc, .csv, .txt, .xlsx)"
    )


@pytest.mark.parametrize(
    "file_path",
    TESTING_FILES,
    ids=[path.name for path in TESTING_FILES] or None,
)
def test_extract_testing_file(file_path):
    """Extract each file in testing_files/ and print response (use pytest -s)."""
    result = extract_local_file(file_path)

    print(f"\n--- {file_path.name} ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("--- end ---\n")

    assert result.get("success") is True, result.get("error", "extraction failed")
    assert result.get("content_length", 0) > 0

    if "Greenberg" in file_path.name:
        _assert_greenberg_template(result["content"])
