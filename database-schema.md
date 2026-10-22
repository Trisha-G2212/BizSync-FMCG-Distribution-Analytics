# BizSync — Database Schema

## Entity-relationship overview

```
Distributor 1───* Retailer
Distributor 1───* Inventory *───1 Product
Retailer    1───* Order *───1 Distributor
Order       1───* OrderItem *───1 Product
SalesTransaction *───1 Retailer, *───1 Distributor, *───1 Product
StockMovement *───1 Product, *───1 Distributor
User (independent — referenced loosely by TroubleshootingIssue.reported_by/assigned_to)
TroubleshootingIssue (standalone operational log)
```

## Tables

### users
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| name | varchar(120) | not null |
| email | varchar(160) | unique, not null, indexed |
| password_hash | varchar(255) | not null (bcrypt, never plaintext) |
| role | enum(user_role) | not null |
| created_at | timestamptz | default now() |

### products
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| product_code | varchar(30) | unique, not null, indexed |
| name | varchar(150) | not null |
| category | varchar(60) | not null, indexed |
| brand | varchar(80) | not null |
| unit_price | numeric(10,2) | not null |
| cost_price | numeric(10,2) | not null |
| reorder_level | integer | default 20 |
| active | boolean | default true |
| created_at | timestamptz | default now() |

Composite index on `(category, active)` — the two columns most list/filter
queries actually query by together.

### distributors
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| distributor_code | varchar(30) | unique, not null, indexed |
| name, contact_person, phone, email | varchar | not null |
| city | varchar(80) | not null, indexed |
| state | varchar(80) | not null |
| status | enum(distributor_status) | default ACTIVE |
| created_at | timestamptz | default now() |

### retailers
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| retailer_code | varchar(30) | unique, not null, indexed |
| name, owner_name, phone | varchar | not null |
| city | varchar(80) | not null, indexed |
| state | varchar(80) | not null |
| distributor_id | integer | FK → distributors.id, not null, indexed |
| status | enum(retailer_status) | default ACTIVE |
| created_at | timestamptz | default now() |

### inventory
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| product_id | integer | FK → products.id, not null, indexed |
| distributor_id | integer | FK → distributors.id, not null, indexed |
| quantity | integer | default 0 |
| reserved_quantity | integer | default 0 |
| last_updated | timestamptz | default now(), auto-updates |

**Unique constraint on `(product_id, distributor_id)`** — each distributor
has exactly one stock record per product, enforced at the database level.
`available = quantity - reserved_quantity` is the value order confirmation
actually checks against.

### orders
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| order_number | varchar(30) | unique, not null, indexed |
| retailer_id | integer | FK → retailers.id, not null, indexed |
| distributor_id | integer | FK → distributors.id, not null, indexed |
| order_date | date | default current_date, indexed |
| status | enum(order_status) | default PENDING, indexed |
| total_amount | numeric(12,2) | default 0 |
| created_at | timestamptz | default now() |

Valid `status` values: `PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED,
CANCELLED` — enforced as a native Postgres enum type, not just an
application-level check.

### order_items
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| order_id | integer | FK → orders.id, not null, indexed |
| product_id | integer | FK → products.id, not null, indexed |
| quantity | integer | not null |
| unit_price | numeric(10,2) | not null |
| subtotal | numeric(12,2) | not null |

`unit_price` is stored here independently of `products.unit_price` — if a
product's price changes later, historical orders must not silently
change value.

### sales_transactions
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| transaction_date | date | not null, indexed |
| retailer_id | integer | FK → retailers.id, not null, indexed |
| distributor_id | integer | FK → distributors.id, not null, indexed |
| product_id | integer | FK → products.id, not null, indexed |
| quantity | integer | not null |
| revenue, cost, profit | numeric(12,2) | not null |
| created_at | timestamptz | default now() |

### stock_movements
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| product_id | integer | FK → products.id, not null, indexed |
| distributor_id | integer | FK → distributors.id, not null, indexed |
| movement_type | enum(movement_type) | not null, indexed |
| quantity | integer | not null (positive = inbound, negative = outbound) |
| reference_id | integer | nullable, loosely typed (see below) |
| timestamp | timestamptz | default now(), indexed |

`reference_id` is intentionally not a strict foreign key: a movement's
origin varies by type (an order ID for SALE, nothing for a manual Excel
PURCHASE import). A strict FK would force three separate nullable FK
columns instead of one flexible one.

### troubleshooting_issues
| Column | Type | Constraints |
|---|---|---|
| id | integer | PK |
| title | varchar(200) | not null |
| description | text | not null |
| severity | enum(issue_severity) | not null, indexed |
| module | varchar(80) | not null, indexed |
| status | enum(issue_status) | default OPEN, indexed |
| reported_by, assigned_to | integer | FK → users.id, nullable |
| created_at | timestamptz | default now() |
| resolved_at | timestamptz | nullable, auto-set/cleared by the service layer |
| root_cause, resolution | text | nullable |

## Why create_all() instead of Alembic migrations

The schema was designed once, up front, for a project with a fixed scope —
Alembic's versioned migration history earns its complexity in a system
whose schema changes incrementally over years in production. `create_all()`
is explicitly documented by SQLAlchemy as appropriate for this case: it
creates tables that don't exist yet, never touches ones that do, and is
safe to run repeatedly (verified in Phase 2 testing).
