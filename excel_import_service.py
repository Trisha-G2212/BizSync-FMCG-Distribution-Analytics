"""
Excel import service.

WHY VALIDATE EVERY ROW BEFORE WRITING ANY OF THEM (per-row, not
per-file): a real Excel upload from a distributor might have 1000 rows
where only 23 are broken. Rejecting the WHOLE file because of 23 bad
rows would be unusable in practice — the spec's own example output
("965 successfully imported, 35 failed") confirms partial success is
the intended behavior. Each row is validated independently; only rows
that pass every check get written to the database, inside one
transaction for the whole batch (so a crash mid-import can't leave the
database in an inconsistent state, but a few genuinely bad rows never
block the hundreds of good ones).

WHY DUPLICATE DETECTION HAPPENS DIFFERENTLY PER ENTITY: Products,
Retailers, and Inventory are MASTER DATA — re-uploading a product with
an existing product_code is a normal "update this product's price"
operation (upsert). Sales transactions are FINANCIAL RECORDS — the
troubleshooting issue seeded in Phase 3 ("Inventory mismatch after
Excel import... duplicate transaction IDs") is specifically about this
distinction: importing the same sale twice must never double-count
revenue. So sales import requires a transaction_id column used purely
to detect duplicates WITHIN the uploaded file — it's the exact
scenario that seeded issue describes.
"""
import pandas as pd
from io import BytesIO
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.retailer import Retailer
from app.models.distributor import Distributor
from app.models.inventory import Inventory
from app.models.sales_transaction import SalesTransaction
from app.models.stock_movement import StockMovement
from app.models.enums import RetailerStatus, MovementType
from app.schemas.excel_import import ImportSummary, RowError


def _to_summary(processed, imported, duplicates, invalid_rows, errors) -> ImportSummary:
    return ImportSummary(
        records_processed=processed,
        successfully_imported=imported,
        failed=duplicates + invalid_rows,
        duplicates=duplicates,
        invalid_rows=invalid_rows,
        errors=errors,
    )


def _read_excel(file_bytes: bytes, required_columns: list) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes))
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required column(s): {', '.join(missing_cols)}")
    return df


def import_products(db: Session, file_bytes: bytes) -> ImportSummary:
    required = ["product_code", "name", "category", "brand", "unit_price", "cost_price"]
    df = _read_excel(file_bytes, required)

    errors = []
    seen_codes = set()
    imported = 0
    duplicates = 0
    invalid = 0

    for idx, row in df.iterrows():
        excel_row = idx + 2  # +1 for 0-index, +1 for header row

        code = str(row.get("product_code", "")).strip()
        if not code or code == "nan":
            errors.append(RowError(row=excel_row, message="product_code missing"))
            invalid += 1
            continue

        if code in seen_codes:
            errors.append(RowError(row=excel_row, message=f"duplicate product_code '{code}' within file"))
            duplicates += 1
            continue
        seen_codes.add(code)

        name = str(row.get("name", "")).strip()
        category = str(row.get("category", "")).strip()
        brand = str(row.get("brand", "")).strip()
        if not name or name == "nan":
            errors.append(RowError(row=excel_row, message="name missing"))
            invalid += 1
            continue
        if not category or category == "nan":
            errors.append(RowError(row=excel_row, message="category missing"))
            invalid += 1
            continue

        try:
            unit_price = Decimal(str(row["unit_price"]))
            cost_price = Decimal(str(row["cost_price"]))
            if unit_price <= 0 or cost_price <= 0:
                raise InvalidOperation()
        except (InvalidOperation, ValueError, TypeError):
            errors.append(RowError(row=excel_row, message="unit_price and cost_price must be positive numbers"))
            invalid += 1
            continue

        reorder_level = row.get("reorder_level")
        reorder_level = int(reorder_level) if pd.notna(reorder_level) else 20

        existing = db.query(Product).filter(Product.product_code == code).one_or_none()
        if existing:
            existing.name = name
            existing.category = category
            existing.brand = brand
            existing.unit_price = unit_price
            existing.cost_price = cost_price
            existing.reorder_level = reorder_level
        else:
            db.add(Product(
                product_code=code, name=name, category=category, brand=brand,
                unit_price=unit_price, cost_price=cost_price, reorder_level=reorder_level,
            ))
        imported += 1

    db.flush()
    return _to_summary(len(df), imported, duplicates, invalid, errors)


def import_retailers(db: Session, file_bytes: bytes) -> ImportSummary:
    required = ["retailer_code", "name", "owner_name", "phone", "city", "state", "distributor_code"]
    df = _read_excel(file_bytes, required)

    distributor_lookup = {d.distributor_code: d.id for d in db.query(Distributor).all()}

    errors = []
    seen_codes = set()
    imported = 0
    duplicates = 0
    invalid = 0

    for idx, row in df.iterrows():
        excel_row = idx + 2
        code = str(row.get("retailer_code", "")).strip()

        if not code or code == "nan":
            errors.append(RowError(row=excel_row, message="retailer_code missing"))
            invalid += 1
            continue
        if code in seen_codes:
            errors.append(RowError(row=excel_row, message=f"duplicate retailer_code '{code}' within file"))
            duplicates += 1
            continue
        seen_codes.add(code)

        dist_code = str(row.get("distributor_code", "")).strip()
        if dist_code not in distributor_lookup:
            errors.append(RowError(row=excel_row, message=f"distributor_code '{dist_code}' does not exist"))
            invalid += 1
            continue

        name = str(row.get("name", "")).strip()
        if not name or name == "nan":
            errors.append(RowError(row=excel_row, message="name missing"))
            invalid += 1
            continue

        existing = db.query(Retailer).filter(Retailer.retailer_code == code).one_or_none()
        payload = dict(
            name=name,
            owner_name=str(row.get("owner_name", "")).strip(),
            phone=str(row.get("phone", "")).strip(),
            city=str(row.get("city", "")).strip(),
            state=str(row.get("state", "")).strip(),
            distributor_id=distributor_lookup[dist_code],
        )
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            db.add(Retailer(retailer_code=code, status=RetailerStatus.ACTIVE, **payload))
        imported += 1

    db.flush()
    return _to_summary(len(df), imported, duplicates, invalid, errors)


def import_sales(db: Session, file_bytes: bytes) -> ImportSummary:
    """See module docstring — transaction_id is used ONLY to catch
    duplicates within this upload; it isn't persisted, since
    SalesTransaction doesn't need it after import-time validation."""
    required = ["transaction_id", "transaction_date", "retailer_code", "distributor_code",
                "product_code", "quantity", "revenue", "cost"]
    df = _read_excel(file_bytes, required)

    retailer_lookup = {r.retailer_code: r.id for r in db.query(Retailer).all()}
    distributor_lookup = {d.distributor_code: d.id for d in db.query(Distributor).all()}
    product_lookup = {p.product_code: p.id for p in db.query(Product).all()}

    errors = []
    seen_txn_ids = set()
    imported = 0
    duplicates = 0
    invalid = 0

    for idx, row in df.iterrows():
        excel_row = idx + 2
        txn_id = str(row.get("transaction_id", "")).strip()

        if not txn_id or txn_id == "nan":
            errors.append(RowError(row=excel_row, message="transaction_id missing"))
            invalid += 1
            continue
        if txn_id in seen_txn_ids:
            errors.append(RowError(row=excel_row, message=f"duplicate transaction_id '{txn_id}' within file"))
            duplicates += 1
            continue
        seen_txn_ids.add(txn_id)

        retailer_code = str(row.get("retailer_code", "")).strip()
        distributor_code = str(row.get("distributor_code", "")).strip()
        product_code = str(row.get("product_code", "")).strip()

        if retailer_code not in retailer_lookup:
            errors.append(RowError(row=excel_row, message=f"retailer_code '{retailer_code}' does not exist"))
            invalid += 1
            continue
        if distributor_code not in distributor_lookup:
            errors.append(RowError(row=excel_row, message=f"distributor_code '{distributor_code}' does not exist"))
            invalid += 1
            continue
        if product_code not in product_lookup:
            errors.append(RowError(row=excel_row, message=f"product_code '{product_code}' does not exist"))
            invalid += 1
            continue

        try:
            quantity = int(row["quantity"])
            revenue = Decimal(str(row["revenue"]))
            cost = Decimal(str(row["cost"]))
            if quantity <= 0:
                raise ValueError()
        except (ValueError, TypeError, InvalidOperation):
            errors.append(RowError(row=excel_row, message="quantity must be a positive integer, revenue/cost must be numeric"))
            invalid += 1
            continue

        try:
            txn_date = pd.to_datetime(row["transaction_date"]).date()
        except Exception:
            errors.append(RowError(row=excel_row, message="transaction_date is not a valid date"))
            invalid += 1
            continue

        db.add(SalesTransaction(
            transaction_date=txn_date,
            retailer_id=retailer_lookup[retailer_code],
            distributor_id=distributor_lookup[distributor_code],
            product_id=product_lookup[product_code],
            quantity=quantity,
            revenue=revenue,
            cost=cost,
            profit=(revenue - cost).quantize(Decimal("0.01")),
        ))
        imported += 1

    db.flush()
    return _to_summary(len(df), imported, duplicates, invalid, errors)


def import_inventory(db: Session, file_bytes: bytes) -> ImportSummary:
    """Each row represents new stock ARRIVING (a purchase/receiving
    event) — it ADDS to existing quantity rather than overwriting it,
    and writes a PURCHASE StockMovement for audit purposes, exactly
    like a manual purchase would (see stock_movement.py model)."""
    required = ["product_code", "distributor_code", "quantity"]
    df = _read_excel(file_bytes, required)

    distributor_lookup = {d.distributor_code: d.id for d in db.query(Distributor).all()}
    product_lookup = {p.product_code: p.id for p in db.query(Product).all()}

    errors = []
    imported = 0
    invalid = 0

    for idx, row in df.iterrows():
        excel_row = idx + 2
        product_code = str(row.get("product_code", "")).strip()
        distributor_code = str(row.get("distributor_code", "")).strip()

        if product_code not in product_lookup:
            errors.append(RowError(row=excel_row, message=f"product_code '{product_code}' does not exist"))
            invalid += 1
            continue
        if distributor_code not in distributor_lookup:
            errors.append(RowError(row=excel_row, message=f"distributor_code '{distributor_code}' does not exist"))
            invalid += 1
            continue

        try:
            quantity = int(row["quantity"])
            if quantity <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            errors.append(RowError(row=excel_row, message="quantity must be a positive integer"))
            invalid += 1
            continue

        product_id = product_lookup[product_code]
        distributor_id = distributor_lookup[distributor_code]

        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id, Inventory.distributor_id == distributor_id
        ).one_or_none()
        if inventory:
            inventory.quantity += quantity
        else:
            db.add(Inventory(product_id=product_id, distributor_id=distributor_id, quantity=quantity))

        db.add(StockMovement(
            product_id=product_id, distributor_id=distributor_id,
            movement_type=MovementType.PURCHASE, quantity=quantity, reference_id=None,
        ))
        imported += 1

    db.flush()
    return _to_summary(len(df), imported, 0, invalid, errors)


IMPORTERS: dict[str, Callable] = {
    "products": import_products,
    "retailers": import_retailers,
    "sales": import_sales,
    "inventory": import_inventory,
}
