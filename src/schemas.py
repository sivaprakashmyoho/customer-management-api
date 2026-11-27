
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime


# Schema for creating a customer
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    city: str | None = None


# Schema for updating a customer
class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    city: str | None = None


# Schema for returning customer details
class CustomerOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    city: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
