"""
Generates sample Excel files for the Excel Import feature, with a few
deliberately broken rows in each — this is what gives the validation
pipeline something real to catch (rather than only ever seeing perfect
data, which proves nothing).

Usage:
    python -m app.generate_sample_excel
"""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_products():
    rows = [
        {"product_code": "PRD0051", "name": "Horlicks Health Drink 500g", "category": "Beverages", "brand": "HUL", "unit_price": 220.00, "cost_price": 165.00, "reorder_level": 20},
        {"product_code": "PRD0052", "name": "Bournvita 500g", "category": "Beverages", "brand": "Mondelez", "unit_price": 210.00, "cost_price": 158.00, "reorder_level": 20},
        {"product_code": "PRD0053", "name": "Britannia Marie Gold 250g", "category": "Snacks", "brand": "Britannia", "unit_price": 40.00, "cost_price": 28.00, "reorder_level": 30},
        # Deliberately broken rows, matching the spec's own examples:
        {"product_code": "", "name": "Missing Code Product", "category": "Snacks", "brand": "TestBrand", "unit_price": 50.00, "cost_price": 30.00, "reorder_level": 20},  # Row: product_code missing
        {"product_code": "PRD0054", "name": "Bad Price Product", "category": "Snacks", "brand": "TestBrand", "unit_price": -10.00, "cost_price": 30.00, "reorder_level": 20},  # Row: negative price
        {"product_code": "PRD0051", "name": "Duplicate Code Product", "category": "Beverages", "brand": "HUL", "unit_price": 100.00, "cost_price": 70.00, "reorder_level": 20},  # duplicate within file
    ]
    pd.DataFrame(rows).to_excel(OUTPUT_DIR / "products.xlsx", index=False)


def generate_retailers():
    rows = [
        {"retailer_code": "RTL0101", "name": "New Star General Store", "owner_name": "Suresh Kumar", "phone": "9876543210", "city": "Bengaluru", "state": "Karnataka", "distributor_code": "DIST001"},
        {"retailer_code": "RTL0102", "name": "City Mini Mart", "owner_name": "Anita Rao", "phone": "9876543211", "city": "Mumbai", "state": "Maharashtra", "distributor_code": "DIST002"},
        # Broken rows:
        {"retailer_code": "RTL0103", "name": "Bad Distributor Store", "owner_name": "Ravi Shah", "phone": "9876543212", "city": "Chennai", "state": "Tamil Nadu", "distributor_code": "DIST999"},  # Row: distributor_code does not exist
        {"retailer_code": "", "name": "Missing Code Store", "owner_name": "Priya Nair", "phone": "9876543213", "city": "Pune", "state": "Maharashtra", "distributor_code": "DIST002"},  # Row: retailer_code missing
    ]
    pd.DataFrame(rows).to_excel(OUTPUT_DIR / "retailers.xlsx", index=False)


def generate_sales():
    rows = [
        {"transaction_id": "TXN9001", "transaction_date": "2026-08-01", "retailer_code": "RTL0001", "distributor_code": "DIST001", "product_code": "PRD0001", "quantity": 10, "revenue": 3023.20, "cost": 2611.80},
        {"transaction_id": "TXN9002", "transaction_date": "2026-08-02", "retailer_code": "RTL0002", "distributor_code": "DIST001", "product_code": "PRD0002", "quantity": 5, "revenue": 1500.00, "cost": 1200.00},
        # Broken rows, matching the spec's own examples:
        {"transaction_id": "TXN9003", "transaction_date": "2026-08-03", "retailer_code": "RTL9999", "distributor_code": "DIST001", "product_code": "PRD0001", "quantity": 3, "revenue": 900.00, "cost": 700.00},  # Row: retailer_code does not exist
        {"transaction_id": "TXN9004", "transaction_date": "2026-08-04", "retailer_code": "RTL0001", "distributor_code": "DIST001", "product_code": "PRD0001", "quantity": -2, "revenue": 500.00, "cost": 400.00},  # Row: quantity must be positive
        {"transaction_id": "TXN9002", "transaction_date": "2026-08-05", "retailer_code": "RTL0002", "distributor_code": "DIST001", "product_code": "PRD0002", "quantity": 5, "revenue": 1500.00, "cost": 1200.00},  # Row: duplicate transaction
    ]
    pd.DataFrame(rows).to_excel(OUTPUT_DIR / "sales.xlsx", index=False)


def generate_inventory():
    rows = [
        {"product_code": "PRD0001", "distributor_code": "DIST001", "quantity": 100},
        {"product_code": "PRD0002", "distributor_code": "DIST001", "quantity": 50},
        # Broken rows:
        {"product_code": "PRD9999", "distributor_code": "DIST001", "quantity": 30},  # Row: product_code does not exist
        {"product_code": "PRD0003", "distributor_code": "DIST001", "quantity": -5},  # Row: quantity must be positive
    ]
    pd.DataFrame(rows).to_excel(OUTPUT_DIR / "inventory.xlsx", index=False)


if __name__ == "__main__":
    generate_products()
    generate_retailers()
    generate_sales()
    generate_inventory()
    print(f"Sample Excel files generated in: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.xlsx")):
        print(f"  - {f.name}")
