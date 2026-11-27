import os
import secrets

from dotenv import load_dotenv
from fastapi.security import APIKeyHeader


from src.schemas import CustomerCreate, CustomerOut, CustomerUpdate

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
from src.models import Customer
from src.schemas import CustomerCreate, CustomerOut

load_dotenv()

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
    api_key: str = Depends(verify_api_key)


# Create a customer
@app.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db)
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
    api_key: str = Depends(verify_api_key)

    return new_customer


# Get all customers
# Get customer by ID
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
    api_key: str = Depends(verify_api_key)

    return customer

# Get all customers
@app.get("/customers", response_model=list[CustomerOut])
def get_customers(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    customers = db.query(Customer).all()
    return customers
# Update customer
@app.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db)
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
    api_key: str = Depends(verify_api_key)

    return customer

@app.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
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
    api_key: str = Depends(verify_api_key)

    return {"message": "Customer deleted successfully"}