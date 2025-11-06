import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Perfume Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "perfume-commerce"}

# Seed some demo products if collection is empty
@app.on_event("startup")
def seed_products():
    try:
        if db is None:
            return
        count = db["product"].count_documents({})
        if count == 0:
            demo: List[dict] = [
                {
                    "name": "Glass No. 1",
                    "price": 128,
                    "rating": 4.8,
                    "reviews": 214,
                    "notes": "Iridescent citrus with crystalline musk.",
                    "image": "https://images.unsplash.com/photo-1584961818182-12c443d7d1fc?auto=format&fit=crop&w=1600&q=80",
                    "description": "A luminous blend of yuzu zest, white tea, and clean musk.",
                    "topNotes": ["Yuzu", "White Tea", "Pear"],
                    "baseNotes": ["Crystal Musk", "Ambroxan"],
                    "in_stock": True,
                },
                {
                    "name": "Glass No. 2",
                    "price": 142,
                    "rating": 4.6,
                    "reviews": 167,
                    "notes": "Soft lilac over cool mineral woods.",
                    "image": "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=1600&q=80",
                    "description": "Translucent florals meet clean woods for a balanced aura.",
                    "topNotes": ["Lilac", "Bergamot"],
                    "baseNotes": ["Atlas Cedar", "Mineral Woods"],
                    "in_stock": True,
                },
                {
                    "name": "Glass No. 3",
                    "price": 156,
                    "rating": 4.9,
                    "reviews": 298,
                    "notes": "Sheer vanilla with airy iris and salt.",
                    "image": "https://images.unsplash.com/photo-1643114451805-f14ea7bb0dfb?auto=format&fit=crop&w=1600&q=80",
                    "description": "Weightless warmth with vanilla absolute and iris.",
                    "topNotes": ["Iris", "Sea Salt"],
                    "baseNotes": ["Vanilla Absolute", "Cashmere Woods"],
                    "in_stock": True,
                },
            ]
            for d in demo:
                create_document("product", d)
    except Exception as e:
        # Non-fatal; continue if seeding fails
        print("Seed error:", e)

@app.get("/products")
def list_products(limit: Optional[int] = None):
    docs = get_documents("product", {}, limit)
    # Convert ObjectId to str
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return {"items": docs}

class CheckoutRequest(BaseModel):
    items: List[dict]
    customer: dict

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    # Calculate subtotal server-side for trust
    subtotal = 0.0
    product_prices = {}
    ids = [it.get("id") for it in payload.items]
    if not ids:
        raise HTTPException(status_code=400, detail="Cart is empty")
    # Fetch product prices by name match (demo) or id if present
    products = get_documents("product")
    by_name = {p["name"]: p for p in products}
    for it in payload.items:
        name = it.get("name")
        qty = int(it.get("qty", 1))
        prod = by_name.get(name)
        if not prod:
            raise HTTPException(status_code=400, detail=f"Product not found: {name}")
        subtotal += float(prod["price"]) * qty
    order = Order(
        items=[{"product_id": by_name[it["name"]]["_id"].__str__(), "qty": int(it.get("qty", 1))} for it in payload.items],
        customer=payload.customer,  # type: ignore
        subtotal=round(subtotal, 2),
        status="paid",  # demo assumes immediate payment success
        payment_ref="demo-paid",
    )
    order_id = create_document("order", order)
    return {"status": "success", "order_id": order_id, "subtotal": order.subtotal}

@app.get("/test")
def test_database():
    from database import db as _db
    ok = _db is not None
    collections = []
    try:
        if ok:
            collections = _db.list_collection_names()
    except Exception:
        collections = []
    return {"backend": "running", "database": "connected" if ok else "unavailable", "collections": collections}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
