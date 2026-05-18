# Testing files

Place sample documents here for local extraction tests.

Supported extensions: `.pdf`, `.docx`, `.doc`, `.csv`, `.txt`, `.xlsx`

```bash
# Extract and print all files
python run_local_extract.py

# Extract one file
python run_local_extract.py "your-file.xlsx"

# Pytest (prints JSON with -s)
pytest test_testing_files.py -s
```
