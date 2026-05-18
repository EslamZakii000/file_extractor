"""
Extract local files from testing_files/ and print API-style responses.

Usage:
  python run_local_extract.py                    # all files in testing_files/
  python run_local_extract.py myfile.xlsx        # one file (name or path)
"""
import json
import sys
from pathlib import Path

from app import detect_file_extension, ensure_file_extension_path, try_extract_with_fallback

ROOT = Path(__file__).resolve().parent
TESTING_FILES_DIR = ROOT / "testing_files"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".csv", ".txt", ".xlsx"}


def list_testing_files():
    """Return supported files from testing_files/, sorted by name."""
    if not TESTING_FILES_DIR.is_dir():
        return []
    return sorted(
        path
        for path in TESTING_FILES_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith(".")
    )


def resolve_testing_file_path(name_or_path: str) -> Path:
    """Resolve a filename or path against testing_files/ and project root."""
    candidate = Path(name_or_path)
    if candidate.is_file():
        return candidate.resolve()

    for base in (TESTING_FILES_DIR, ROOT):
        path = (base / candidate).resolve()
        if path.is_file():
            return path

    return candidate.resolve()


def extract_local_file(file_path: Path) -> dict:
    file_path = file_path.resolve()
    if not file_path.is_file():
        return {"success": False, "error": f"File not found: {file_path}"}

    extension = detect_file_extension(str(file_path))
    working_path = ensure_file_extension_path(str(file_path), extension)
    extension = Path(working_path).suffix.lower() or extension

    content, detected_ext, error = try_extract_with_fallback(working_path, extension)

    if error:
        return {
            "success": False,
            "error": error,
            "file_type": detected_ext or extension,
            "source_file": str(file_path),
        }

    if content is None:
        return {
            "success": False,
            "error": "Unsupported file type or failed to extract content",
            "file_type": detected_ext or extension,
            "source_file": str(file_path),
        }

    return {
        "success": True,
        "content": content,
        "file_type": detected_ext or extension,
        "content_length": len(content),
        "source_file": str(file_path),
    }


def print_result(file_path: Path, result: dict) -> None:
    print(f"\n=== {file_path.name} ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) > 1:
        target = resolve_testing_file_path(sys.argv[1])
        if not target.is_file():
            print(f"File not found: {sys.argv[1]}")
            print(f"Looked in: {TESTING_FILES_DIR}")
            sys.exit(1)

        result = extract_local_file(target)
        print_result(target, result)
        if not result.get("success"):
            sys.exit(1)
        return

    files = list_testing_files()
    if not files:
        print(
            f"No supported files found in {TESTING_FILES_DIR}\n"
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
        sys.exit(1)

    failed = 0
    for file_path in files:
        result = extract_local_file(file_path)
        print_result(file_path, result)
        if not result.get("success"):
            failed += 1

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
