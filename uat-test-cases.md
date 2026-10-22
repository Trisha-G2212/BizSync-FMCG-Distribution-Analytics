# BizSync — User Acceptance Testing (UAT) Test Cases

**Document status:** All test cases below were executed against the real
application (live PostgreSQL database, live FastAPI backend, live React
frontend) during development — not written speculatively. Several entries
reference actual bugs found and fixed during this process, which is normal
and expected: UAT exists to catch exactly this kind of issue.

**Test environment:** Local development (Windows, Python 3.14, Node.js,
PostgreSQL 18), backend on `localhost:8000`, frontend on `localhost:3000`.

**Test accounts used:**
| Email | Password | Role |
|---|---|---|
| admin@bizsync.com | admin123 | ADMIN |
| priya.manager@bizsync.com | manager123 | SALES_MANAGER |
| rahul.rep@bizsync.com | rep123 | SALES_REP |
| ananya.analyst@bizsync.com | analyst123 | ANALYST |

---

### TC-01: Login with valid credentials

| Field | Detail |
|---|---|
| **Preconditions** | Backend and database running; seeded admin user exists |
| **Steps** | 1. Navigate to `/login`.<br>2. Enter `admin@bizsync.com` / `admin123`.<br>3. Click Sign In. |
| **Expected Result** | Redirected to `/`, dashboard loads, sidebar shows user's name and role (ADMIN) with a Log out button |
| **Actual Result** | As expected. Backend returned a signed JWT; frontend stored it and called `/auth/me`, confirming identity before rendering the dashboard |
| **Status** | ✅ Pass |

---

### TC-02: Login with invalid credentials

| Field | Detail |
|---|---|
| **Preconditions** | Backend running |
| **Steps** | 1. Navigate to `/login`.<br>2. Enter `admin@bizsync.com` with a wrong password.<br>3. Click Sign In. |
| **Expected Result** | Login rejected with a generic "Incorrect email or password" message; no token issued |
| **Actual Result** | As expected — HTTP 401 returned. Note: the backend deliberately returns the *same* message whether the email doesn't exist or the password is wrong, to avoid letting an attacker discover which emails have accounts |
| **Status** | ✅ Pass |

---

### TC-03: Add product

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ADMIN or SALES_MANAGER |
| **Steps** | 1. Go to Products.<br>2. Click "+ Add Product".<br>3. Fill in a unique product code, name, category, brand, unit price, cost price.<br>4. Click Save. |
| **Expected Result** | Product appears in the table; HTTP 201 returned |
| **Actual Result** | As expected — verified both via automated browser test and manual testing |
| **Status** | ✅ Pass |

---

### TC-04: Duplicate product code

| Field | Detail |
|---|---|
| **Preconditions** | A product with code `PRD0001` already exists |
| **Steps** | 1. Go to Products → Add Product.<br>2. Enter `PRD0001` as the product code (already in use).<br>3. Fill remaining fields, click Save. |
| **Expected Result** | Save rejected with a clear "already exists" message; no duplicate row created |
| **Actual Result** | As expected — HTTP 409 Conflict, verified via direct API test before frontend was even built |
| **Status** | ✅ Pass |

---

### TC-05: Create retailer

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ADMIN or SALES_MANAGER; at least one distributor exists |
| **Steps** | 1. Go to Retailers → Add Retailer.<br>2. Fill in retailer code, name, owner, phone, city, state.<br>3. Select a distributor from the dropdown.<br>4. Click Save. |
| **Expected Result** | Retailer created and linked to the selected distributor |
| **Actual Result** | As expected |
| **Status** | ✅ Pass |

---

### TC-06: Create order

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ADMIN, SALES_MANAGER, or SALES_REP; retailers, distributors, and products exist |
| **Steps** | 1. Go to Orders → "+ Create Order".<br>2. Select a retailer and distributor.<br>3. Add one or more product lines with quantities.<br>4. Click Create Order. |
| **Expected Result** | Order created with status PENDING; total calculated correctly from current product prices |
| **Actual Result** | As expected. Verified the live total preview matched the order's actual stored `total_amount` after creation |
| **Status** | ✅ Pass |

---

### TC-07: Order with insufficient inventory

| Field | Detail |
|---|---|
| **Preconditions** | A product/distributor combination with known low stock (e.g. 10 units available) |
| **Steps** | 1. Create an order requesting MORE than available stock (e.g. 15 units of a product with only 10 in stock).<br>2. Attempt to Confirm the order. |
| **Expected Result** | Order creation succeeds (orders don't check stock until confirmation); confirmation is rejected with a clear message stating available vs. requested quantity; inventory remains unchanged |
| **Actual Result** | As expected — HTTP 409 with message "Insufficient inventory for product X: 10 available, 15 requested." Verified directly that inventory quantity was untouched after the rejected confirmation, proving the transaction rollback works correctly |
| **Status** | ✅ Pass |

---

### TC-08: Confirm order / inventory update after order

| Field | Detail |
|---|---|
| **Preconditions** | A PENDING order exists for a product with sufficient stock |
| **Steps** | 1. Note the product's current inventory quantity.<br>2. Confirm the order.<br>3. Re-check the product's inventory quantity. |
| **Expected Result** | Order status becomes CONFIRMED; inventory quantity decreases by exactly the ordered amount; a StockMovement audit record is created |
| **Actual Result** | As expected. Additionally stress-tested: two order confirmations for the same limited-stock product were fired *simultaneously* (concurrent requests) — exactly one succeeded, the other was correctly rejected, and inventory never went negative. This confirms the `SELECT ... FOR UPDATE` row-locking genuinely prevents overselling under concurrent load, not just in the simple sequential case |
| **Status** | ✅ Pass |

---

### TC-09: Excel upload (valid data)

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ADMIN or SALES_MANAGER; a well-formed products.xlsx file available |
| **Steps** | 1. Go to Excel Import.<br>2. Select "Products" as the data type.<br>3. Choose a valid Excel file.<br>4. Click Upload & Import. |
| **Expected Result** | Import summary shows all rows successfully imported; products appear in the Products list |
| **Actual Result** | As expected for well-formed rows within the sample file |
| **Status** | ✅ Pass |

---

### TC-10: Invalid Excel upload

| Field | Detail |
|---|---|
| **Preconditions** | A products.xlsx file containing deliberately broken rows: one missing `product_code`, one with a negative price, one duplicate code |
| **Steps** | 1. Go to Excel Import → Products.<br>2. Upload the file with broken rows.<br>3. Review the import summary. |
| **Expected Result** | Valid rows import successfully; broken rows are rejected individually with row-specific error messages (not a whole-file failure); summary shows correct counts (processed / imported / failed / duplicates / invalid) |
| **Actual Result** | As expected — of 6 rows, 3 imported, 3 failed (1 duplicate + 2 invalid), each with the exact row number and a specific message (e.g. "Row 5: product_code missing"). Re-uploading the same file with an updated price for an existing product correctly updated that record rather than creating a duplicate |
| **Status** | ✅ Pass |

---

### TC-11: Dashboard filtering

| Field | Detail |
|---|---|
| **Preconditions** | Logged in; sales/order data exists |
| **Steps** | 1. Go to Dashboard.<br>2. Observe KPI cards and charts load with real aggregated data. |
| **Expected Result** | All figures (revenue, orders, top products, top retailers, category breakdown, distributor performance) are calculated correctly |
| **Actual Result** | As expected, with one bug found and fixed during testing: an earlier version of the distributor/retailer performance queries joined Orders and SalesTransactions in a single query, causing a "fan-out" that inflated revenue figures far beyond the real total (a distributor showing ₹23M in revenue against a company-wide total of ₹5.9M). Rewritten as separate aggregations merged by ID; all six dashboard endpoints were then verified against independently hand-written SQL queries with exact matches |
| **Status** | ✅ Pass (after fix) |

---

### TC-12: Low-stock detection

| Field | Detail |
|---|---|
| **Preconditions** | At least one product/distributor combination with `quantity - reserved_quantity <= reorder_level` |
| **Steps** | 1. Go to Inventory.<br>2. Check the "Low stock only" checkbox. |
| **Expected Result** | Only inventory rows meeting the low-stock rule are shown; the count matches the Dashboard's "Low Stock Items" KPI |
| **Actual Result** | As expected — both figures independently verified against the same SQL rule and matched (86 items) |
| **Status** | ✅ Pass |

---

### TC-13: Cancel order

| Field | Detail |
|---|---|
| **Preconditions** | An order in PENDING, CONFIRMED, or PROCESSING status |
| **Steps** | 1. Go to Orders.<br>2. Click "Cancel" on an eligible order.<br>3. Confirm the cancellation prompt. |
| **Expected Result** | Order status becomes CANCELLED; no further status changes possible (dead-end state, matching the defined workflow) |
| **Actual Result** | As expected. Also verified the reverse case: attempting to skip stages (e.g. CONFIRMED directly to DELIVERED) or to act on an already-CANCELLED/DELIVERED order is correctly rejected with HTTP 409 |
| **Status** | ✅ Pass |

---

### TC-14: Resolve troubleshooting issue

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ADMIN or ANALYST; an OPEN issue exists |
| **Steps** | 1. Go to Troubleshooting.<br>2. Open an issue.<br>3. Fill in Root Cause and Resolution.<br>4. Change status to Resolved.<br>5. Save. |
| **Expected Result** | Issue status updates to RESOLVED; `resolved_at` timestamp is automatically set by the server |
| **Actual Result** | As expected. Also confirmed a SALES_REP account can report a new issue but is correctly blocked (HTTP 403) from updating status/root-cause/resolution — only ADMIN/ANALYST may do so |
| **Status** | ✅ Pass |

---

### TC-15: Role-based access control (write actions)

| Field | Detail |
|---|---|
| **Preconditions** | Logged in as ANALYST (a read-only role per the spec) |
| **Steps** | 1. Attempt to create a product via the API directly (bypassing UI) with a valid ANALYST token. |
| **Expected Result** | Request rejected with HTTP 403, regardless of UI state |
| **Actual Result** | As expected. This was tested both at the API level directly (to confirm the real security boundary) and through the UI (where the "+ Add Product" button is hidden entirely for ANALYST accounts via `RoleGate`) — confirming the two layers agree: the UI hides what the API would reject anyway |
| **Status** | ✅ Pass |

---

## Summary

| Total Test Cases | Passed | Failed | Notes |
|---|---|---|---|
| 15 | 15 | 0 | 2 real bugs found and fixed during test execution (dashboard fan-out query, Excel-import bytes handling) — both are discussed in `docs/troubleshooting.md` |

**Interview note:** the value of this document isn't that everything passed on the first try — it's that testing *found real issues* (the fan-out bug, a module-field length validation gap, a pandas bytes-handling bug) before they reached production, which is exactly what UAT and integration testing are for.
