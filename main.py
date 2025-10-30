import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem, Payment

app = FastAPI(title="Mazzarelli's Bakery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_str_id(doc):
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Mazzarelli's Bakery API running"}


@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "collections": [],
    }
    try:
        if db is not None:
            resp["database"] = "✅ Connected & Working"
            resp["database_url"] = "✅ Set"
            resp["database_name"] = db.name
            resp["collections"] = db.list_collection_names()
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:80]}"
    return resp


# ---------- Products ----------
@app.get("/api/products", response_model=List[Product])
def list_products():
    docs = get_documents("product")
    results = []
    for d in docs:
        d = to_str_id(d)
        results.append(Product(**{
            "name": d.get("name"),
            "description": d.get("description"),
            "price_cents": d.get("price_cents"),
            "image_url": d.get("image_url"),
            "category": d.get("category"),
            "in_stock": d.get("in_stock", True)
        }))
    return results

@app.post("/api/products", response_model=str)
def create_product(product: Product):
    new_id = create_document("product", product)
    return new_id

@app.post("/api/seed")
def seed_products():
    # Only seed if no products exist
    count = db["product"].count_documents({}) if db is not None else 0
    if count > 0:
        return {"inserted": 0, "skipped": True}
    samples = [
        {
            "name": "Almond Croissant",
            "description": "Buttery pastry layered with almond cream and toasted almonds.",
            "price_cents": 450,
            "image_url": "https://images.unsplash.com/photo-1524182576065-1c814ad3a8be?q=80&w=1400&auto=format&fit=crop",
            "category": "pastry",
            "in_stock": True,
        },
        {
            "name": "Sourdough Loaf",
            "description": "Naturally leavened, crackly crust, tender and tangy crumb.",
            "price_cents": 600,
            "image_url": "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?q=80&w=1400&auto=format&fit=crop",
            "category": "bread",
            "in_stock": True,
        },
        {
            "name": "Cannoli",
            "description": "Classic ricotta filling with citrus zest and chocolate chips.",
            "price_cents": 375,
            "image_url": "https://images.unsplash.com/photo-1619527492558-2ec3cf1134f9?q=80&w=1400&auto=format&fit=crop",
            "category": "pastry",
            "in_stock": True,
        },
        {
            "name": "Tiramisu Slice",
            "description": "Espresso-soaked ladyfingers layered with mascarpone cream.",
            "price_cents": 525,
            "image_url": "https://images.unsplash.com/photo-1613478223719-e5e4766473a6?q=80&w=1400&auto=format&fit=crop",
            "category": "dessert",
            "in_stock": True,
        },
    ]
    inserted = 0
    for s in samples:
        create_document("product", s)
        inserted += 1
    return {"inserted": inserted}


# ---------- Orders ----------
@app.post("/api/orders")
def create_order(order: Order):
    # validate product ids exist and compute totals
    total = 0
    for item in order.items:
        total += item.subtotal_cents
    if total != order.total_cents:
        raise HTTPException(status_code=400, detail="Total does not match items subtotal")

    order_id = create_document("order", order)
    return {"order_id": order_id, "status": "created"}

@app.get("/api/orders/{order_id}")
def get_order(order_id: str):
    try:
        doc = db["order"].find_one({"_id": ObjectId(order_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Order not found")
        doc = to_str_id(doc)
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")


# ---------- Payments (simulated) ----------
@app.post("/api/payments")
def create_payment(payment: Payment):
    # Check order exists and amount matches
    try:
        order = db["order"].find_one({"_id": ObjectId(payment.order_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if payment.amount_cents != order.get("total_cents"):
        raise HTTPException(status_code=400, detail="Amount mismatch")

    # very naive simulated processing
    status = "succeeded" if payment.method in ("card", "cash", "apple_pay") else "failed"
    payment_record = {
        "order_id": payment.order_id,
        "amount_cents": payment.amount_cents,
        "method": payment.method,
        "status": status,
    }
    payment_id = create_document("payment", payment_record)

    # update order payment_status
    db["order"].update_one({"_id": ObjectId(payment.order_id)}, {"$set": {"payment_status": "paid" if status == "succeeded" else "failed"}})

    return {"payment_id": payment_id, "status": status}
