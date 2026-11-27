
import os
import hmac
import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure test environment before importing the application
os.environ["API_KEY"] = "test-api-key"
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"

from src.main import app
from src.database import Base, get_db


# Separate in-memory SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# Override the application's database dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

API_HEADERS = {
    "X-API-Key": "test-api-key"
}


# Reset database before every test
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# Helper function to create customers
def create_test_customer(
    name="Arun Kumar",
    email="arun@example.com"
):
    return client.post(
        "/customers",
        headers=API_HEADERS,
        json={
            "name": name,
            "email": email,
            "phone": "9876543210",
            "city": "Pondicherry"
        }
    )


# --------------------------------------------------
# 1. HEALTH CHECK TEST
# --------------------------------------------------

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"


# --------------------------------------------------
# 2. CREATE CUSTOMER TESTS
# --------------------------------------------------

def test_create_customer():
    response = create_test_customer()

    assert response.status_code == 201
    assert response.json()["name"] == "Arun Kumar"
    assert response.json()["email"] == "arun@example.com"


def test_create_duplicate_customer_email():
    create_test_customer()

    response = create_test_customer(
        name="Another Customer"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


def test_create_customer_invalid_email():
    response = client.post(
        "/customers",
        headers=API_HEADERS,
        json={
            "name": "Arun",
            "email": "invalid-email"
        }
    )

    assert response.status_code == 422


def test_create_customer_missing_name():
    response = client.post(
        "/customers",
        headers=API_HEADERS,
        json={
            "email": "arun@example.com"
        }
    )

    assert response.status_code == 422


# --------------------------------------------------
# 3. GET ALL CUSTOMERS TESTS
# --------------------------------------------------

def test_get_all_customers():
    create_test_customer()

    response = client.get(
        "/customers",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_customers_pagination():
    create_test_customer("Arun", "arun@example.com")
    create_test_customer("Bala", "bala@example.com")
    create_test_customer("Kumar", "kumar@example.com")

    response = client.get(
        "/customers?page=1&per_page=2",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


# --------------------------------------------------
# 4. GET CUSTOMER BY ID TESTS
# --------------------------------------------------

def test_get_customer_by_id():
    created = create_test_customer()
    customer_id = created.json()["id"]

    response = client.get(
        f"/customers/{customer_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["id"] == customer_id


def test_get_customer_not_found():
    response = client.get(
        "/customers/9999",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


# --------------------------------------------------
# 5. UPDATE CUSTOMER TESTS
# --------------------------------------------------

def test_update_customer():
    created = create_test_customer()
    customer_id = created.json()["id"]

    response = client.put(
        f"/customers/{customer_id}",
        headers=API_HEADERS,
        json={
            "name": "Arun Updated"
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Arun Updated"


def test_update_customer_not_found():
    response = client.put(
        "/customers/9999",
        headers=API_HEADERS,
        json={
            "name": "Updated Name"
        }
    )

    assert response.status_code == 404


def test_update_customer_duplicate_email():
    create_test_customer(
        "Arun",
        "arun@example.com"
    )

    second = create_test_customer(
        "Bala",
        "bala@example.com"
    )

    customer_id = second.json()["id"]

    response = client.put(
        f"/customers/{customer_id}",
        headers=API_HEADERS,
        json={
            "email": "arun@example.com"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


# --------------------------------------------------
# 6. DELETE CUSTOMER TESTS
# --------------------------------------------------

def test_delete_customer():
    created = create_test_customer()
    customer_id = created.json()["id"]

    response = client.delete(
        f"/customers/{customer_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Customer deleted successfully"


def test_delete_customer_not_found():
    response = client.delete(
        "/customers/9999",
        headers=API_HEADERS
    )

    assert response.status_code == 404


# --------------------------------------------------
# 7. API KEY AUTHENTICATION TESTS
# --------------------------------------------------

def test_missing_api_key():
    response = client.get("/customers")

    assert response.status_code == 401


def test_invalid_api_key():
    response = client.get(
        "/customers",
        headers={
            "X-API-Key": "wrong-api-key"
        }
    )

    assert response.status_code == 401


# --------------------------------------------------
# 8. WEBHOOK TESTS
# --------------------------------------------------

def generate_signature(payload):
    return hmac.new(
        b"test-webhook-secret",
        payload,
        hashlib.sha256
    ).hexdigest()


def test_webhook_valid_signature():
    payload = json.dumps({
        "event": "customer.created",
        "customer_id": 1
    }).encode("utf-8")

    response = client.post(
        "/webhooks/customer-events",
        content=payload,
        headers={
            "X-Signature": generate_signature(payload),
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted"
    }


def test_webhook_tampered_payload():
    original_payload = b'{"event":"customer.created","customer_id":1}'

    signature = generate_signature(original_payload)

    tampered_payload = b'{"event":"customer.created","customer_id":999}'

    response = client.post(
        "/webhooks/customer-events",
        content=tampered_payload,
        headers={
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 401


def test_webhook_missing_signature():
    payload = b'{"event":"customer.created","customer_id":1}'

    response = client.post(
        "/webhooks/customer-events",
        content=payload
    )

    assert response.status_code == 401
