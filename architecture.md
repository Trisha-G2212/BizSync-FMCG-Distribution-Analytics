# BizSync — Architecture

## 1. High-level shape

```
React SPA (Axios) ──HTTP/JSON──▶ FastAPI (routers → services → repositories) ──SQL──▶ PostgreSQL
                                         ▲
                                  Pandas/OpenPyXL (Excel import)
```

Three tiers, each replaceable independently: the frontend only knows REST
endpoints exist, the backend only knows SQLAlchemy models exist, and
PostgreSQL only knows SQL. This is what lets each layer be tested, deployed,
or even rewritten in isolation.

## 2. Backend layering

Every feature (Products, Orders, Excel Import, Dashboard, ...) is split into
three files:

```
routers/<feature>.py       HTTP layer only — path/query params, status codes,
                            translating service exceptions into HTTPExceptions
services/<feature>_service.py   Business rules — duplicate checks, workflow
                            transitions, transaction-safety logic
repositories/<feature>_repository.py   Raw SQLAlchemy queries — no HTTP
                            concepts, no business rules
```

**Why this split matters in practice:** `order_service.py`'s
`_confirm_order_and_update_inventory()` has no idea it's being called from
an HTTP PATCH request — it just raises a plain Python exception
(`InsufficientInventoryError`) if something's wrong. The router is the only
place that decides that exception means HTTP 409. If BizSync ever grew a
CLI tool or a scheduled batch job that needed to confirm orders
programmatically, it could call `order_service.update_order_status()`
directly — the same business logic, zero HTTP baggage.

## 3. The most important piece: order confirmation transaction safety

This is the part of the codebase most worth explaining in an interview.

```
PATCH /api/orders/{id}/status {status: CONFIRMED}
  → router calls order_service.update_order_status()
    → for each order line item:
        SELECT inventory row ... FOR UPDATE   (locks the row)
        check quantity - reserved_quantity >= requested
    → if ANY item fails: raise InsufficientInventoryError
      (nothing has been written yet — nothing to undo)
    → if ALL items pass: deduct inventory, write StockMovement rows,
      set order.status = CONFIRMED
  → router calls db.commit() on success, db.rollback() on any exception
```

`SELECT ... FOR UPDATE` is a Postgres row lock: while one transaction holds
it, a second transaction trying to lock the *same* row simply waits. This
is what was proven — not just claimed — during Phase 8 testing: two
confirmation requests fired at the exact same instant against
limited stock resulted in exactly one success and one clean rejection,
with final inventory never going negative.

## 4. Why validate everything before writing anything

A naive implementation might deduct inventory for line item 1, then
discover line item 2 doesn't have enough stock, and have to somehow undo
item 1's deduction. BizSync's order confirmation logic checks **every**
line item first, and only writes anything once all of them pass. Combined
with the single `db.commit()`/`db.rollback()` at the router level, this
guarantees an order confirmation is atomic: either the whole order's
inventory is correctly deducted, or none of it is — there is no partial
state.

## 5. Why FastAPI, PostgreSQL, and React specifically

- **FastAPI**: async-native, Pydantic-based request/response validation
  built in, and free auto-generated OpenAPI/Swagger docs — meaning the API
  is self-documenting by construction, not by separate effort.
- **PostgreSQL**: real foreign keys, unique constraints, and row-level
  locking (`SELECT ... FOR UPDATE`) are load-bearing features of this
  app, not optional extras — a document database or a simpler key-value
  store couldn't provide the same correctness guarantees for orders and
  inventory.
- **React**: component-based UI matches the app's actual shape (Products
  page, Orders page, Dashboard, ... are genuinely separate concerns), and
  Axios interceptors give one central place to attach auth tokens and
  handle 401s across the whole app.

## 6. Authentication flow

```
POST /api/auth/login {email, password}
  → auth_service verifies password against bcrypt hash
  → issues a JWT containing {sub: user_id, email, role}, signed with
    JWT_SECRET_KEY, expiring in JWT_EXPIRE_MINUTES

Every subsequent request:
  Authorization: Bearer <token>
  → get_current_user dependency decodes + verifies the signature/expiry
  → require_role(...) dependency checks the decoded role against an
    allow-list before the route body ever executes
```

The frontend never decodes the token itself — it just stores it and lets
Axios attach it to every request. Role-based UI hiding (`RoleGate`
component) is presentational only; the actual security boundary is the
backend's `require_role` dependency, verified independently via direct
API tests in Phase 5 (not just by observing the UI hide a button).

## 7. Excel import pipeline

```
Upload file → pandas reads it into a DataFrame → required-columns check
  (whole-file failure if missing) → per-row validation loop:
    - missing required fields?
    - duplicate key within this file?
    - foreign key (e.g. distributor_code) actually exists?
    - values in valid ranges (positive prices/quantities)?
  → valid rows: insert or update (upsert) for master data (Products,
    Retailers, Inventory); strict reject-on-duplicate for Sales
    Transactions (financial records must never be double-counted)
  → return a summary: processed / imported / failed / duplicates /
    invalid, plus a row-by-row error list
```

Products/Retailers/Inventory upsert on re-import (re-uploading is a normal
"update this data" operation). Sales Transactions never upsert — a
duplicate `transaction_id` within a file is always rejected, because
double-importing a sale would silently inflate revenue. This distinction
was deliberately tested in Phase 13's test suite.

## 8. Performance decisions

- **Pagination everywhere**: every list endpoint takes `page`/`page_size`
  and applies `LIMIT`/`OFFSET` in SQL — the app never loads an entire
  table into memory to slice it in Python.
- **Dashboard aggregation happens in SQL**: `SUM`/`COUNT`/`GROUP BY` run
  inside Postgres, not by fetching raw rows and summing them in Python.
- **Avoiding join fan-out**: a real bug found in Phase 10 — joining
  Orders and SalesTransactions in one query multiplied rows and inflated
  revenue sums. Fixed by computing each aggregation as an independent
  query and merging by ID in Python — still O(n), never re-fetching raw
  transaction rows.
