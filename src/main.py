import hmac
import hashlib
import json

from fastapi import Request, BackgroundTasks

import os
import secrets

from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
from src.models import Customer
from src.schemas import CustomerCreate, CustomerOut, CustomerUpdate

load_dotenv()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(
    api_key: str | None = Depends(api_key_header)
):
    expected_api_key = os.getenv("API_KEY")

    if (
        not expected_api_key
        or not api_key
        or not secrets.compare_digest(api_key, expected_api_key)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    return api_key

app = FastAPI(
    title="Customer Management API",
    description="API for managing customer records",
    version="1.0.0"
)

def process_customer_event(event_data: dict):
    print("Processing customer event in background...")

    print("Event data:", event_data)

    print("Customer event processed successfully")

@app.post("/webhooks/customer-events")
async def receive_customer_event(
    request: Request,
    background_tasks: BackgroundTasks
):
    # Read raw request body
    body = await request.body()

    # Read signature header
    received_signature = request.headers.get("X-Signature")

    # Check missing signature or secret
    if not received_signature or not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    # Generate expected HMAC-SHA256 signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures securely
    if not hmac.compare_digest(
        expected_signature,
        received_signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    # Parse JSON only after signature validation
    try:
        event_data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    # Process event in background
    background_tasks.add_task(
        process_customer_event,
        event_data
    )

    return {
        "status": "accepted"
    }

# Health check
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

# Create a customer

@app.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    new_customer = Customer(
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        city=customer.city
    )

    db.add(new_customer)

    try:
        db.commit()
        db.refresh(new_customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    return new_customer



# Get all customers
# Get customer by ID
@app.get("/customers", response_model=list[CustomerOut])
def get_customers(
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    if page < 1 or per_page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page and per_page must be greater than 0"
        )

    customers = (
        db.query(Customer)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return customers

@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer
# Update customer

@app.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    update_data = customer_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(customer, key, value)

    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    return customer


@app.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    db.delete(customer)
    db.commit()

    return {"message": "Customer deleted successfully"}
