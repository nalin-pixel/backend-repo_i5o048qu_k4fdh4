"""
Database Schemas

Each Pydantic model below represents a MongoDB collection.
Collection name = lowercase of class name (e.g., Product -> "product").
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class Product(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., ge=0, description="Price in USD")
    rating: float = Field(0, ge=0, le=5, description="Average rating 0-5")
    reviews: int = Field(0, ge=0, description="Number of reviews")
    notes: Optional[str] = Field(None, description="Short aroma note summary")
    image: Optional[str] = Field(None, description="Primary image URL")
    description: Optional[str] = Field(None, description="Long description")
    topNotes: List[str] = Field(default_factory=list, description="Top notes")
    baseNotes: List[str] = Field(default_factory=list, description="Base notes")
    in_stock: bool = Field(True, description="Whether product is available")

class OrderItem(BaseModel):
    product_id: str
    qty: int = Field(..., ge=1)

class Customer(BaseModel):
    name: str
    email: str
    address: Optional[str] = None

class Order(BaseModel):
    items: List[OrderItem]
    customer: Customer
    subtotal: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status: pending, paid, failed")
    payment_ref: Optional[str] = Field(None, description="External payment reference if any")
