"""Tests for the Excel import validation pipeline."""
import io
import pandas as pd


def make_excel_bytes(rows: list) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(rows).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.read()


def test_import_valid_products(client, admin_headers):
    file_bytes = make_excel_bytes([
        {"product_code": "IMP001", "name": "Imported Product", "category": "Snacks",
         "brand": "TestBrand", "unit_price": 50.0, "cost_price": 30.0},
    ])
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["successfully_imported"] == 1
    assert body["failed"] == 0


def test_import_catches_missing_product_code(client, admin_headers):
    file_bytes = make_excel_bytes([
        {"product_code": "", "name": "No Code", "category": "Snacks",
         "brand": "TestBrand", "unit_price": 50.0, "cost_price": 30.0},
    ])
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    body = response.json()
    assert body["invalid_rows"] == 1
    assert "product_code missing" in body["errors"][0]["message"]


def test_import_catches_duplicate_within_file(client, admin_headers):
    file_bytes = make_excel_bytes([
        {"product_code": "IMP002", "name": "First", "category": "Snacks", "brand": "B", "unit_price": 50.0, "cost_price": 30.0},
        {"product_code": "IMP002", "name": "Duplicate", "category": "Snacks", "brand": "B", "unit_price": 50.0, "cost_price": 30.0},
    ])
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    body = response.json()
    assert body["successfully_imported"] == 1
    assert body["duplicates"] == 1


def test_import_catches_negative_price(client, admin_headers):
    file_bytes = make_excel_bytes([
        {"product_code": "IMP003", "name": "Bad Price", "category": "Snacks", "brand": "B", "unit_price": -5, "cost_price": 30.0},
    ])
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    body = response.json()
    assert body["invalid_rows"] == 1


def test_import_rejects_missing_required_columns(client, admin_headers):
    file_bytes = make_excel_bytes([{"wrong_column": "value"}])
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 400


def test_import_rejects_non_excel_file(client, admin_headers):
    response = client.post(
        "/api/import/products", headers=admin_headers,
        files={"file": ("notexcel.txt", b"just some text", "text/plain")},
    )
    assert response.status_code == 400


def test_import_forbidden_for_analyst(client, analyst_headers):
    file_bytes = make_excel_bytes([
        {"product_code": "IMP004", "name": "X", "category": "Snacks", "brand": "B", "unit_price": 50.0, "cost_price": 30.0},
    ])
    response = client.post(
        "/api/import/products", headers=analyst_headers,
        files={"file": ("products.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 403
