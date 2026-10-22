# BizSync — Troubleshooting Log

Every entry below is a real issue found during this project's development
(not written speculatively), following the Problem → Root Cause →
Resolution structure the Troubleshooting module itself uses. This log
exists both as genuine documentation and as evidence that the project's
testing process actually caught real defects before they reached
production — which is the whole point of testing.

---

### Issue: Inventory mismatch after Excel import
**Module:** Excel Import | **Severity:** High

**Problem:** Distributor-reported stock counts didn't match system
inventory after a bulk Excel upload of purchase records.

**Root Cause:** Duplicate transaction IDs existed in the uploaded Excel
file, causing the same purchase to be applied to inventory twice.

**Resolution:** Added duplicate-detection validation (by transaction ID,
scoped to within the uploaded file) to the Excel import pipeline, before
any database insert occurs. Sales Transaction imports strictly reject
duplicates rather than upserting — unlike master data (Products,
Retailers), a financial record must never be silently double-counted.

---

### Issue: Dashboard distributor/retailer revenue figures inflated ("fan-out" join bug)
**Module:** Analytics Dashboard | **Severity:** High

**Problem:** During Phase 10 development, the distributor-performance
endpoint returned a single distributor's revenue as ₹23,793,198 — while
total company-wide revenue was only ₹5,937,428. Clearly impossible.

**Root Cause:** The query joined `Orders` and `SalesTransactions` to a
`Distributor` in a single SQL statement. When a distributor has, say, 5
orders and 20 sales transactions, that join produces up to 100 combined
rows — and `SUM(revenue)` summed across all 100 rows, multiplying the
real total roughly 20x.

**Resolution:** Rewrote the query as two independent aggregations (one for
order counts, one for revenue), merged by distributor ID in application
code. Verified the fix by cross-checking every dashboard endpoint's output
against hand-written, independently-computed SQL queries — all matched
exactly. A permanent regression test (`test_dashboard.py`) now seeds a
known exact revenue total and asserts it returns unmultiplied.

---

### Issue: pandas `read_excel` fails on uploaded file bytes
**Module:** Excel Import | **Severity:** Medium

**Problem:** Every Excel import request failed immediately with `Expected
file path name or file-like object, got <class 'bytes'>`.

**Root Cause:** `pandas.read_excel()` expects a file path or a file-like
object — not raw bytes. The upload handler was passing the raw bytes read
from the uploaded file directly.

**Resolution:** Wrapped the bytes in `io.BytesIO()` before passing to
`pd.read_excel()`. Caught immediately by testing against a real uploaded
file rather than only reviewing the code.

---

### Issue: bcrypt/passlib version incompatibility during seed data generation
**Module:** Authentication | **Severity:** Medium

**Problem:** Running the seed script failed while hashing passwords for
seeded demo users.

**Root Cause:** `passlib`'s bcrypt backend detection reads an internal
`__about__.__version__` attribute that newer `bcrypt` releases removed —
a known compatibility break between the two libraries.

**Resolution:** Dropped `passlib` entirely and call `bcrypt.hashpw()` /
`bcrypt.checkpw()` directly — fewer moving parts, and sidesteps the
incompatibility completely.

---

### Issue: Swagger's "Authorize" dialog didn't match the login endpoint
**Module:** Authentication | **Severity:** Low

**Problem:** Clicking "Authorize" in Swagger UI showed a username/password
OAuth2 form, but the actual `/auth/login` endpoint expects JSON
`{email, password}` — the two didn't match, and the dialog couldn't
actually authenticate against the real endpoint.

**Root Cause:** The security scheme was declared as `OAuth2PasswordBearer`,
which auto-generates an OAuth2-style form in Swagger, regardless of what
the login endpoint actually expects.

**Resolution:** Switched to `HTTPBearer`, which makes Swagger show a
single plain "paste your token" field — matching the real intended flow
(call `/auth/login` separately, copy the token, paste it in).

---

### Issue: Postgres health check always targets the wrong database
**Module:** Docker / Infrastructure | **Severity:** Low

**Problem:** The Postgres container logged repeated `FATAL: database
"bizsync_user" does not exist` errors on every health-check interval.

**Root Cause:** `pg_isready -U bizsync_user` (with no `-d` flag) defaults
to checking a database with the *same name as the user* — which never
existed; only a database named `bizsync` does.

**Resolution:** Added the missing `-d bizsync` flag. Verified directly
that `pg_isready`'s exit code was actually `0` (healthy) in both the
broken and fixed versions — meaning this was log noise, not a functional
blocker, but still worth fixing for a clean deployment log.

---

### Issue: Frontend pie chart renders blank
**Module:** Analytics Dashboard | **Severity:** Low

**Problem:** The "Revenue by Category" pie chart rendered as an empty box,
while every bar/line chart on the same dashboard page worked correctly
with the same underlying data. Found by manual testing, not automated
tests.

**Root Cause:** The backend serializes `Decimal` fields as JSON strings
(e.g. `"1295183.84"`) to avoid floating-point precision loss — correct
for an API response. Recharts' `<Pie>` component specifically requires
real JavaScript numbers to compute slice angles, and fails silently
(renders nothing, no console error) when given a numeric string. Bar and
Line charts happen to tolerate the string via implicit coercion, which is
why only the pie chart was affected.

**Resolution:** Explicitly converted every numeric field to a real number
(`Number(...)`) when the dashboard data is received, before it reaches
any chart component.

---

### Issue: Module field accepts values exceeding the database column limit
**Module:** Troubleshooting | **Severity:** Low

**Problem:** Reporting an issue with an unusually long "Module" value
(a copy-paste mistake) failed with a raw, unfriendly database error:
`StringDataRightTruncation: value too long for type character
varying(80)`.

**Root Cause:** The `module` column is correctly limited to 80 characters
at the database level, but the frontend form had no matching client-side
limit — so a value that was always going to be rejected reached the
database before failing, producing a confusing raw SQL error instead of a
clear validation message.

**Resolution:** Added `maxLength={80}` to the frontend input, matching the
actual database constraint, so the mistake is prevented before submission
rather than surfacing as a database error afterward.

---

### Issue: SQLAlchemy session sharing broke automated tests
**Module:** Backend Testing | **Severity:** Medium

**Problem:** Tests exercising the order-confirmation error path (`test_
confirm_order_with_insufficient_inventory_is_rejected`) failed with
`Could not refresh instance` and `transaction already deassociated from
connection` warnings.

**Root Cause:** FastAPI's `TestClient` runs synchronous route handlers in
a separate worker thread from the test's own thread. The test fixtures
were sharing one SQLAlchemy `Session` object between the test and the
simulated HTTP request — and Sessions are not thread-safe, so the app's
own `db.rollback()` call (correctly triggered by the insufficient-
inventory check) corrupted the test's view of the transaction.

**Resolution:** Gave every simulated HTTP request its own fresh `Session`
(exactly mirroring how `app.database.get_db()` works in real production
request handling), rather than forcing the test and the app to share one.
This is both the fix and, arguably, a more faithful test of real
production behavior than the original shared-session approach.

---

## Patterns worth noting across these issues

- **Several bugs were only caught by testing against real data or real
  requests** — not by code review alone (the pandas bytes issue, the pie
  chart, the fan-out query). This is the concrete argument for the
  testing investment described in `docs/uat-test-cases.md`.
- **Financial/audit-critical logic (Sales Transactions, StockMovement)
  is deliberately less forgiving** than master data (Products,
  Retailers) — duplicates are rejected outright rather than merged,
  because silently double-counting revenue is worse than rejecting a
  re-upload.
- **Frontend validation limits were added to mirror backend constraints
  exactly** (the module-length case) — the goal is never to duplicate
  business logic in two places, only to give the user a clear message
  before a request that was always going to fail reaches the server.
