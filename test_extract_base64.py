import base64
import json
import os
import tempfile

import pytest

from app import app, CONFIG

try:
    from openpyxl import Workbook
    XLSX_CREATE_AVAILABLE = True
except ImportError:
    XLSX_CREATE_AVAILABLE = False


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def auth_headers():
    """Return auth headers when API key auth is enabled."""
    api_key = CONFIG.get("FILE_EXTRACTOR_KEY", "")
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def test_extract_base64_txt_success(client):
    """Extract text from a raw base64 payload."""
    original_text = "Hello from base64 endpoint"
    payload = base64.b64encode(original_text.encode("utf-8")).decode("utf-8")

    response = client.post(
        "/extract-base64",
        headers=auth_headers(),
        json={
            "base64": payload,
            "filename": "sample.txt",
            "contentType": "text/plain",
        },
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["file_type"] == ".txt"
    assert original_text in data["content"]
    assert data["content_length"] > 0


def test_extract_base64_xlsx_success(client):
    """Extract cell values from a base64-encoded XLSX payload."""
    if not XLSX_CREATE_AVAILABLE:
        pytest.skip("openpyxl not available for creating test files")

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Product", "Qty"])
        sheet.append(["Widget", 42])
        workbook.save(temp_path)

        with open(temp_path, "rb") as file_handle:
            payload = base64.b64encode(file_handle.read()).decode("utf-8")

        response = client.post(
            "/extract-base64",
            headers=auth_headers(),
            json={
                "base64": payload,
                "filename": "inventory.xlsx",
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["file_type"] == ".xlsx"
        assert "Widget" in data["content"]
        assert "42" in data["content"]
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_extract_base64_data_url_success(client):
    """Extract text from a data URL base64 payload."""
    original_text = "Data URL test content"
    payload = base64.b64encode(original_text.encode("utf-8")).decode("utf-8")
    data_url = f"data:text/plain;base64,{payload}"

    response = client.post(
        "/extract-base64",
        headers=auth_headers(),
        json={
            "base64": data_url,
            "filename": "data-url.txt",
        },
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["file_type"] == ".txt"
    assert original_text in data["content"]


def test_extract_base64_missing_payload(client):
    """Return 400 when base64 is missing."""
    response = client.post("/extract-base64", headers=auth_headers(), json={})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Missing base64 data" in data["error"]


def test_extract_base64_invalid_payload(client):
    """Return 400 when base64 is invalid."""
    response = client.post(
        "/extract-base64",
        headers=auth_headers(),
        json={"base64": "not-valid-base64%%%"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Invalid base64 data" in data["error"]


def test_extract_base64_file_too_large(client):
    """Return 400 when decoded payload exceeds configured max size."""
    original_max_file_size = CONFIG["MAX_FILE_SIZE"]
    CONFIG["MAX_FILE_SIZE"] = 10

    try:
        oversized_bytes = b"x" * 11
        payload = base64.b64encode(oversized_bytes).decode("utf-8")

        response = client.post(
            "/extract-base64",
            headers=auth_headers(),
            json={"base64": payload, "filename": "large.txt", "contentType": "text/plain"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "File too large" in data["error"]
    finally:
        CONFIG["MAX_FILE_SIZE"] = original_max_file_size
