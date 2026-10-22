"""
Order service — the most safety-critical logic in the whole app.

WHY ORDER CREATION DOESN'T TOUCH INVENTORY AT ALL: placing an order is
just a request — nothing is actually committed to leave the warehouse
yet. Inventory is only ever affected when an order is CONFIRMED (see
confirm_order below). This mirrors a real distribution business: a
retailer can submit an order that later turns out to be unfulfillable;
that's a normal, expected outcome, not a bug.

WHY confirm_order IS WHERE ALL THE TRANSACTION SAFETY LIVES: this is
the one place where an order and physical inventory become linked. The
spec explicitly asks: "Use database transactions so partial updates do
not occur" and "What happens if inventory is insufficient?" — this
function is the concrete answer to both.
"""
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.stock_movement import StockMovement
from app.models.enums import OrderStatus, MovementType
from app.repositories import order_repository, retailer_repository, distributor_repository, product_repository


class OrderNotFoundError(Exception):
    pass


class InvalidRetailerError(Exception):
    pass


class InvalidDistributorError(Exception):
    pass


class InvalidProductError(Exception):
    pass


class InsufficientInventoryError(Exception):
    def __init__(self, product_id: int, available: int, requested: int):
        self.product_id = product_id
        self.available = available
        self.requested = requested
        super().__init__(f"Product {product_id}: only {available} available, {requested} requested")


class InvalidOrderTransitionError(Exception):
    def __init__(self, current: OrderStatus, target: OrderStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot move order from {current.value} to {target.value}")


# The only status transitions the workflow allows, per the spec:
# PENDING -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED, with
# CANCELLED reachable from any pre-shipment state. Defining this as
# data (not scattered if-statements) makes the whole workflow a single
# reviewable table — useful both for correctness and for explaining it
# in an interview.
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def create_order(db: Session, retailer_id: int, distributor_id: int, items_data: list) -> Order:
    """Creates a PENDING order. Deliberately does NOT touch inventory —
    see module docstring. Validates that the retailer, distributor, and
    every product referenced actually exist, so a bad ID fails with a
    clear 422 rather than a raw foreign-key violation from Postgres."""
    if not retailer_repository.get_by_id(db, retailer_id):
        raise InvalidRetailerError(retailer_id)
    if not distributor_repository.get_by_id(db, distributor_id):
        raise InvalidDistributorError(distributor_id)

    order_items = []
    total = Decimal("0")
    for item_data in items_data:
        product = product_repository.get_by_id(db, item_data["product_id"])
        if not product or not product.active:
            raise InvalidProductError(item_data["product_id"])
        subtotal = (product.unit_price * item_data["quantity"]).quantize(Decimal("0.01"))
        total += subtotal
        order_items.append(OrderItem(
            product_id=product.id,
            quantity=item_data["quantity"],
            unit_price=product.unit_price,
            subtotal=subtotal,
        ))

    order = Order(
        order_number=order_repository.get_next_order_number(db),
        retailer_id=retailer_id,
        distributor_id=distributor_id,
        status=OrderStatus.PENDING,
        total_amount=total,
    )
    order_repository.create(db, order)

    for item in order_items:
        item.order_id = order.id
        order_repository.add_item(db, item)

    db.flush()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Order:
    order = order_repository.get_by_id(db, order_id)
    if not order:
        raise OrderNotFoundError(order_id)
    return order


def list_orders(db: Session, page: int, page_size: int, status, retailer_id, distributor_id):
    return order_repository.list_orders(db, page, page_size, status, retailer_id, distributor_id)


def update_order_status(db: Session, order_id: int, new_status: OrderStatus) -> Order:
    """
    Dispatches to the right handler based on the requested transition.
    CONFIRMED is the one transition with real side effects (inventory);
    every other transition is a plain status change.
    """
    order = get_order(db, order_id)

    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise InvalidOrderTransitionError(order.status, new_status)

    if new_status == OrderStatus.CONFIRMED:
        _confirm_order_and_update_inventory(db, order)
    else:
        order.status = new_status
        db.flush()

    return order


def _confirm_order_and_update_inventory(db: Session, order: Order) -> None:
    """
    THE CORE TRANSACTION-SAFETY LOGIC.

    Sequence, all within the caller's single database transaction
    (committed once by the router after this function returns
    successfully, rolled back entirely if anything here raises):

    1. For EVERY line item, lock that product's inventory row for this
       distributor with SELECT ... FOR UPDATE (see order_repository).
    2. Check available stock (quantity - reserved_quantity) against
       the requested quantity. If ANY item fails this check, raise
       immediately — nothing has been written yet, so there is nothing
       to undo.
    3. Only after ALL items pass validation, apply every inventory
       deduction and write a StockMovement audit row per item.
    4. Update the order's status to CONFIRMED.

    WHY VALIDATE EVERYTHING BEFORE WRITING ANYTHING: if item 1 of 3
    passed and got deducted, then item 2 failed, a naive
    implementation would leave inventory partially deducted for an
    order that was never actually confirmed — a real data-integrity
    bug. Validating the whole order first, and only then writing,
    guarantees the order is confirmed atomically: either all of it
    happens, or none of it does.
    """
    insufficient = []
    locked_inventories = {}

    for item in order.items:
        inventory = order_repository.get_inventory_for_update(db, item.product_id, order.distributor_id)
        available = (inventory.quantity - inventory.reserved_quantity) if inventory else 0
        if available < item.quantity:
            insufficient.append((item.product_id, available, item.quantity))
        else:
            locked_inventories[item.product_id] = inventory

    if insufficient:
        # Raising here rolls back the whole transaction at the router
        # level — the locks are released and NOTHING is written, even
        # though we already ran SELECT FOR UPDATE on some rows above.
        product_id, available, requested = insufficient[0]
        raise InsufficientInventoryError(product_id, available, requested)

    for item in order.items:
        inventory = locked_inventories[item.product_id]
        inventory.quantity -= item.quantity
        db.add(StockMovement(
            product_id=item.product_id,
            distributor_id=order.distributor_id,
            movement_type=MovementType.SALE,
            quantity=-item.quantity,
            reference_id=order.id,
        ))

    order.status = OrderStatus.CONFIRMED
    db.flush()
