"""
Database Schemas for Mazzarelli's Bakery

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., Product -> "product").
"""
from typing import List, Optional
from pydantic import BaseModel, Field

# Product catalog
class Product(BaseModel):
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Short description")
    price_cents: int = Field(..., ge=0, description="Price in cents")
    image_url: Optional[str] = Field(None, description="Image URL")
    category: Optional[str] = Field(None, description="Category (bread, pastry, cake, etc.)")
    in_stock: bool = Field(True, description="In stock")

# Line item used inside orders
class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product _id as string")
    name: str
    quantity: int = Field(..., ge=1)
    unit_price_cents: int = Field(..., ge=0)
    subtotal_cents: int = Field(..., ge=0)

# Order collection
class Order(BaseModel):
    items: List[OrderItem]
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    total_cents: int = Field(..., ge=0)
    status: str = Field("new", description="new | preparing | ready | completed | cancelled")
    payment_status: str = Field("unpaid", description="unpaid | pending | paid | failed | refunded")

# Payment intents (simulated)
class Payment(BaseModel):
    order_id: str
    amount_cents: int = Field(..., ge=0)
    method: str = Field("card", description="card | cash | apple_pay (simulated)")
    status: str = Field("pending", description="pending | succeeded | failed")
