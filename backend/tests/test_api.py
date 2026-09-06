from tests.conftest import auth_header


def _order_payload(product_id: int = 1, quantity: int = 1, country: str = "US", name: str = "United States"):
    return {
        "items": [{"product_id": product_id, "quantity": quantity}],
        "shipping_country": country,
        "shipping_country_name": name,
    }


def test_register_and_me(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.user@opspilot.demo",
            "password": "CustomerDemo123!",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "customer" in body["data"]["user"]["roles"]

    headers = {"Authorization": f"Bearer {body['data']['token']['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "new.user@opspilot.demo"


def test_unauthenticated_protected_route(client):
    response = client.get("/api/v1/customer/profile")
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_customer_cannot_access_admin(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    response = client.get("/api/v1/admin/dashboard", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_order_creation_stock_and_idor(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    other_headers = auth_header(client, "ben.harbor@opspilot.demo", "CustomerDemo123!")

    products = client.get("/api/v1/products").json()["data"]["items"]
    product_id = products[0]["id"]
    initial_stock = products[0]["stock_quantity"]

    create = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(product_id, 2),
    )
    assert create.status_code == 200
    order = create.json()["data"]["order"]
    assert order["total_amount"] == "80.00"
    assert order["items"][0]["unit_price"] == "40.00"
    assert order["shipping_country"] == "US"
    assert create.json()["data"]["checkout_url"]

    products_after = client.get("/api/v1/products").json()["data"]["items"]
    assert products_after[0]["stock_quantity"] == initial_stock - 2

    # IDOR: other customer cannot read this order
    forbidden = client.get(f"/api/v1/orders/{order['id']}", headers=other_headers)
    assert forbidden.status_code == 404

    own = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    assert own.status_code == 200


def test_order_requires_shipping_country(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"items": [{"product_id": 1, "quantity": 1}]},
    )
    assert response.status_code == 422


def test_invalid_order_rejected(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(9999, 1),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PRODUCT_UNAVAILABLE"

    inactive = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(2, 1),
    )
    assert inactive.status_code == 400

    overstock = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(1, 999),
    )
    assert overstock.status_code == 400
    assert overstock.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_cancel_restores_stock(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    before = client.get("/api/v1/products").json()["data"]["items"][0]["stock_quantity"]
    created = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(1, 1),
    ).json()["data"]["order"]

    cancelled = client.post(f"/api/v1/orders/{created['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    after = client.get("/api/v1/products").json()["data"]["items"][0]["stock_quantity"]
    assert after == before


def test_admin_status_transition_and_audit(client):
    customer_headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    admin_headers = auth_header(client, "admin@opspilot.demo", "AdminDemo123!")

    create = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json=_order_payload(1, 1),
    )
    assert create.status_code == 200
    order = create.json()["data"]["order"]

    # Unpaid reservation starts as pending; confirm via admin (or Stripe webhook in real flows)
    confirmed = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        headers=admin_headers,
        json={"status": "confirmed"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["current_location"] == "New York, NY, USA"

    bad = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        headers=admin_headers,
        json={"status": "delivered"},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    ok = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        headers=admin_headers,
        json={"status": "processing"},
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["status"] == "processing"

    logs = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert logs.status_code == 200
    actions = [item["action"] for item in logs.json()["data"]["items"]]
    assert "order.status_changed" in actions


def test_abandon_unpaid_checkout(client):
    headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    before = client.get("/api/v1/products").json()["data"]["items"][0]["stock_quantity"]
    created = client.post(
        "/api/v1/orders",
        headers=headers,
        json=_order_payload(1, 1),
    ).json()["data"]["order"]

    abandoned = client.post(f"/api/v1/orders/{created['id']}/abandon-checkout", headers=headers)
    assert abandoned.status_code == 200
    assert abandoned.json()["data"]["status"] == "cancelled"
    assert abandoned.json()["data"]["payment_status"] == "failed"

    after = client.get("/api/v1/products").json()["data"]["items"][0]["stock_quantity"]
    assert after == before


def test_fulfillment_advance_domestic_and_international(client, db_session):
    from datetime import datetime, timedelta, timezone

    from app.models.order import Order, OrderStatus, PaymentStatus
    from app.models.order_item import OrderItem
    from app.models.role import User
    from app.services.fulfillment_service import FulfillmentService

    customer = db_session.query(User).filter_by(email="ava.north@opspilot.demo").one()
    aged = datetime.now(timezone.utc) - timedelta(minutes=15)

    domestic = Order(
        customer_id=customer.id,
        status=OrderStatus.DISPATCHED,
        payment_status=PaymentStatus.PAID,
        total_amount=40,
        shipping_country="US",
        shipping_country_name="United States",
        current_location="Left New York, NY, USA",
        status_changed_at=aged,
        items=[OrderItem(product_id=1, quantity=1, unit_price=40, subtotal=40)],
    )
    international = Order(
        customer_id=customer.id,
        status=OrderStatus.DISPATCHED,
        payment_status=PaymentStatus.PAID,
        total_amount=40,
        shipping_country="CA",
        shipping_country_name="Canada",
        current_location="Left New York, NY, USA",
        status_changed_at=aged,
        items=[OrderItem(product_id=1, quantity=1, unit_price=40, subtotal=40)],
    )
    db_session.add_all([domestic, international])
    db_session.commit()

    result = FulfillmentService(db_session).advance_day(triggered_by="cron", force=False)
    assert result.skipped is False
    assert result.advanced_count == 2

    db_session.refresh(domestic)
    db_session.refresh(international)
    assert domestic.status == OrderStatus.OUT_FOR_DELIVERY
    assert international.status == OrderStatus.IN_TRANSIT_INTERNATIONAL

    second = FulfillmentService(db_session).advance_day(triggered_by="cron", force=False)
    assert second.skipped is True
    assert second.advanced_count == 0


def test_admin_force_advance_and_cancel_after_dispatch(client):
    customer_headers = auth_header(client, "ava.north@opspilot.demo", "CustomerDemo123!")
    admin_headers = auth_header(client, "admin@opspilot.demo", "AdminDemo123!")

    create = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json=_order_payload(1, 1, "CA", "Canada"),
    )
    order_id = create.json()["data"]["order"]["id"]

    for status in ["confirmed", "processing", "dispatched"]:
        patched = client.patch(
            f"/api/v1/admin/orders/{order_id}/status",
            headers=admin_headers,
            json={"status": status},
        )
        assert patched.status_code == 200, patched.text

    # Mark paid so advance_day includes it (admin confirm path does not set paid).
    from app.models.order import Order, PaymentStatus

    # Access through the test client's overridden DB is awkward; use admin advance after marking paid via status chain
    # by patching payment through a direct DB update in a follow-up test fixture approach:
    # Instead, use force advance after setting payment via admin order open + service isn't available.
    # We'll set payment_status through a second order created and admin-marked, using the fulfillment service path
    # already covered above. Here verify cancel blocked after dispatch.
    cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_headers)
    assert cancel.status_code == 400
    assert cancel.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"

    # Create paid-like order for admin advance: confirm + mark paid via pending unpaid then admin path
    create2 = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json=_order_payload(1, 1, "US", "United States"),
    )
    oid2 = create2.json()["data"]["order"]["id"]
    client.patch(
        f"/api/v1/admin/orders/{oid2}/status",
        headers=admin_headers,
        json={"status": "confirmed"},
    )

    # Manually set paid on confirmed order using repository via dependency override session
    # The client fixture shares db_session — get it by creating via SQLAlchemy on app override is hard.
    # Use admin advance after we update payment in a dedicated unit-style call below.
    from app.core.database import get_db

    # Pull the same session from dependency overrides
    gen = client.app.dependency_overrides[get_db]()
    db = next(gen)
    order2 = db.get(Order, oid2)
    order2.payment_status = PaymentStatus.PAID
    db.add(order2)
    db.commit()

    first = client.post("/api/v1/admin/fulfillment/advance-day", headers=admin_headers)
    assert first.status_code == 200
    assert first.json()["data"]["advanced_count"] >= 1
    assert first.json()["data"]["triggered_by"] == "admin"

    detail = client.get(f"/api/v1/orders/{oid2}", headers=customer_headers)
    assert detail.json()["data"]["status"] == "processing"

    second = client.post("/api/v1/admin/fulfillment/advance-day", headers=admin_headers)
    assert second.status_code == 200
    assert second.json()["data"]["advanced_count"] >= 1

    detail2 = client.get(f"/api/v1/orders/{oid2}", headers=customer_headers)
    assert detail2.json()["data"]["status"] == "dispatched"
