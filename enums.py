"""
Shared enums for the domain model.

WHY PYTHON ENUMS + POSTGRES ENUM TYPES:
Using SQLAlchemy's Enum type means Postgres itself enforces valid values
at the database level (a CHECK-constraint-like guarantee), not just in
Python. Two systems could write to this DB (e.g. a future batch job) and
neither could insert an invalid status. This is stronger than just
validating in Pydantic, which only protects API-driven writes.

INTERVIEW ANSWER: "How do you enforce that an order status is always one
of the 6 valid values?" -> "It's a native Postgres ENUM type, generated
from this Python Enum via SQLAlchemy. Invalid values are rejected by the
database, not just the application."
"""
import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SALES_MANAGER = "SALES_MANAGER"
    SALES_REP = "SALES_REP"
    DISTRIBUTOR = "DISTRIBUTOR"
    ANALYST = "ANALYST"


class DistributorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class RetailerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class MovementType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"


class IssueSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
