import os

# Disable in-process fulfillment cron during API tests.
os.environ["FULFILLMENT_CRON_ENABLED"] = "false"
# Avoid live Stripe Checkout calls; use local demo checkout URLs.
os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder"
os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_placeholder"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_placeholder"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import hash_password

get_settings.cache_clear()

from app.main import app
from app.models.product import Product
from app.models.role import Role, User
from app.services import fulfillment_service as fulfillment_service_module
from app.services import order_service as order_service_module

# Modules that cache settings at import time
order_service_module.settings = get_settings()
order_service_module.stripe.api_key = get_settings().stripe_secret_key
fulfillment_service_module.settings = get_settings()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    admin_role = Role(name="admin")
    customer_role = Role(name="customer")
    session.add_all([admin_role, customer_role])
    session.flush()

    admin = User(
        email="admin@opspilot.demo",
        password_hash=hash_password("AdminDemo123!"),
        first_name="Ops",
        last_name="Admin",
        is_active=True,
        roles=[admin_role],
    )
    customer = User(
        email="ava.north@opspilot.demo",
        password_hash=hash_password("CustomerDemo123!"),
        first_name="Ava",
        last_name="North",
        is_active=True,
        roles=[customer_role],
    )
    other = User(
        email="ben.harbor@opspilot.demo",
        password_hash=hash_password("CustomerDemo123!"),
        first_name="Ben",
        last_name="Harbor",
        is_active=True,
        roles=[customer_role],
    )
    product = Product(
        name="Test Beacon",
        slug="test-beacon",
        description="Status beacon",
        price=40,
        stock_quantity=10,
        is_active=True,
        image_urls=["https://example.com/beacon.jpg"],
        specs={"Color": "Teal"},
    )
    inactive = Product(
        name="Retired Hub",
        slug="retired-hub",
        description="Inactive",
        price=20,
        stock_quantity=5,
        is_active=False,
        image_urls=[],
        specs={},
    )
    session.add_all([admin, customer, other, product, inactive])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_header(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["data"]["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
