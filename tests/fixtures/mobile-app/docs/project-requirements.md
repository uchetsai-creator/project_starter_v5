# Project Requirements

## Goals

* Let customers place and track orders without contacting support.
* Give operations staff a single view of order and payment status.

---

## Scope

### In Scope
* Order creation, update, and cancellation
* Payment authorization and refund tracking
* Order status notifications

### Out of Scope
* Warehouse and inventory management
* Marketing and promotions

---

## Roles

| Role | Description |
|---|---|
| Customer | Places orders and views their own order history |
| Support Agent | Views and updates any order on behalf of a customer |
| Admin | Manages catalog data and user accounts |

---

## Business Processes

* **Order Fulfillment**: Order is created, payment is authorized, then the order is queued for shipment.
* **Refund Handling**: Support agent issues a refund, which reverses the payment authorization and updates order status.

---

## Functional Requirements

* **FR-001**: The system must let a customer create an order with one or more line items.
* **FR-002**: The system must authorize payment before an order is marked as confirmed.
* **FR-A01**: The system must let a support agent cancel any order that has not yet shipped.
* **FR-003**: The system must notify the customer by email when order status changes.

---

## Non-Functional Requirements

* **Performance**: p95 API latency under 200ms for order read endpoints.
* **Availability**: 99.9% uptime during business hours.
* **Security**: JWT-based authentication on all endpoints; role checks enforced server-side.
* **Scalability**: Support 10,000 concurrent users during peak sales events.

---

## Edge Cases

### Empty and missing input
* Order submitted with zero line items → reject with a validation error.

### Permission boundaries
* Customer requests another customer's order → return 403 Forbidden.

### Concurrency and race conditions
* Two refund requests submitted for the same order → only the first succeeds; the second is rejected as already-refunded.

### External dependency failures
* Payment provider times out → order stays in "pending payment" and the customer is shown a retry option.

### State machine violations
* Cancellation requested on an already-shipped order → reject with an explanatory error.

### Data contract violations
* Line item references a product ID that no longer exists → reject the order with a clear error identifying the missing product.

---

## Acceptance Criteria

* **AC-001**: Given a valid cart, When the customer submits an order, Then an order is created in "pending payment" status.
* **AC-002**: Given an order in "pending payment", When payment authorization succeeds, Then the order moves to "confirmed" status.

---

## Assumptions

* Payment processing is handled by a third-party provider via API, not built in-house.
* Customers have already created an account before placing an order.
