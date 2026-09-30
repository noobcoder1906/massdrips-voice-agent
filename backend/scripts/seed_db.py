"""
backend/scripts/seed_db.py

Seeds MongoDB with Mass Drips test data.
Uses the app's existing database.py motor client to avoid SSL issues.

Run:
  python -m backend.scripts.seed_db
"""

import asyncio
from datetime import datetime, timezone
from backend.database import connect_to_mongo, close_mongo_connection, get_db

NOW = datetime.now(timezone.utc)

MASS_DRIPS_TENANT = {
    "name":      "Mass Drips",
    "email":     "admin@massdrips.com",
    "phone":     "+91-9999999999",
    "slug":      "mass-drips",
    "persona": {
        "agent_name":  "Aria",
        "brand_name":  "Mass Drips",
        "language":    "hinglish",
        "tone":        "friendly",
        "agent_type":  "sales",
        "max_words":   60,
    },
    "plan":      "pro",
    "is_active": True,
    "created_at": NOW,
    "updated_at": NOW,
}

SAMPLE_LEADS = [
    {
        "name": "Rahul Sharma", "phone": "+91-9876543210", "email": "rahul@example.com",
        "interests": ["oversized tees", "streetwear", "acid wash"],
        "tags": ["warm-lead", "instagram"], "language": "hinglish", "status": "new",
        "notes": "Saw ad on Instagram, clicked Acid Wash Tee",
        "call_count": 0, "lead_score": 0,
    },
    {
        "name": "Priya Verma", "phone": "+91-9123456780", "email": "priya@example.com",
        "interests": ["hoodies", "winter wear"],
        "tags": ["cold-lead"], "language": "english", "status": "new",
        "call_count": 0, "lead_score": 0,
    },
    {
        "name": "Arjun Mehta", "phone": "+91-9012345678",
        "interests": ["cargo pants", "joggers"],
        "tags": ["warm-lead", "referral"], "language": "hindi", "status": "contacted",
        "last_interaction_summary": "Interested in Cargo Joggers. Asked about sizes.",
        "call_count": 1, "lead_score": 20,
    },
    {
        "name": "Sneha Patel", "phone": "+91-8876543210",
        "interests": ["graphic tees", "streetwear"],
        "tags": ["instagram"], "language": "hinglish", "status": "new",
        "call_count": 0, "lead_score": 0,
    },
    {
        "name": "Karan Singh", "phone": "+91-8765432109",
        "interests": ["hoodies", "oversized tees"],
        "tags": ["warm-lead", "repeat-buyer"], "language": "hinglish", "status": "interested",
        "last_interaction_summary": "Bought Acid Wash Tee last month. Looking for a hoodie.",
        "call_count": 2, "lead_score": 45,
    },
]

MASS_DRIPS_PRODUCTS = [
    {
        "name": "OG Acid Wash Tee", "price": 899.0, "currency": "INR",
        "description": "Heavy 280gsm acid wash oversized tee. Unisex fit. Available S-XXL.",
        "category": "T-Shirts", "tags": ["bestseller", "acid-wash", "oversized"],
        "in_stock": True, "sku": "MD-AWT-001",
        "size_chart": {"S": "36-38", "M": "38-40", "L": "40-42", "XL": "42-44", "XXL": "44-46"},
    },
    {
        "name": "Drip Hoodie", "price": 1899.0, "currency": "INR",
        "description": "Fleece-lined premium hoodie with kangaroo pocket. Relaxed streetwear fit.",
        "category": "Hoodies", "tags": ["hoodie", "winter", "premium"],
        "in_stock": True, "sku": "MD-HDR-001",
        "size_chart": {"S": "36-38", "M": "38-40", "L": "40-42", "XL": "42-44"},
    },
    {
        "name": "Cargo Joggers", "price": 1299.0, "currency": "INR",
        "description": "Relaxed fit joggers with 8 pockets. Cotton-poly blend.",
        "category": "Bottoms", "tags": ["cargo", "joggers", "streetwear"],
        "in_stock": True, "sku": "MD-CJG-001",
        "size_chart": {"S": "28-30", "M": "30-32", "L": "32-34", "XL": "34-36"},
    },
    {
        "name": "Graphic Skull Tee", "price": 749.0, "currency": "INR",
        "description": "Bold graphic skull print 100% cotton tee.",
        "category": "T-Shirts", "tags": ["graphic", "skull", "streetwear"],
        "in_stock": True, "sku": "MD-GST-001",
    },
    {
        "name": "Washed Denim Jacket", "price": 2499.0, "currency": "INR",
        "description": "Stone-washed denim jacket with distressed details. Premium quality.",
        "category": "Jackets", "tags": ["denim", "jacket", "premium"],
        "in_stock": True, "sku": "MD-WDJ-001",
    },
    {
        "name": "Tie-Dye Shorts", "price": 699.0, "currency": "INR",
        "description": "Summer-ready tie-dye shorts. Elastic waistband.",
        "category": "Bottoms", "tags": ["shorts", "summer", "tie-dye"],
        "in_stock": True, "sku": "MD-TDS-001",
    },
    {
        "name": "Baggy Cargo Pants", "price": 1499.0, "currency": "INR",
        "description": "Wide-leg cargo pants with utility pockets. Y2K inspired silhouette.",
        "category": "Bottoms", "tags": ["cargo", "baggy", "y2k"],
        "in_stock": True, "sku": "MD-BCP-001",
    },
    {
        "name": "Zip-Up Hoodie", "price": 1699.0, "currency": "INR",
        "description": "Full-zip hoodie with ribbed cuffs. Perfect layering piece.",
        "category": "Hoodies", "tags": ["zip-up", "hoodie"],
        "in_stock": False, "sku": "MD-ZUH-001",
    },
]


async def seed():
    # Use the app's own motor client — avoids separate SSL handshake
    await connect_to_mongo()
    db = get_db()

    print("=" * 50)
    print("VoxSales DB Seeder — Mass Drips Client #1")
    print("=" * 50)

    # ── Tenant ─────────────────────────────────────────────────────────────
    existing = await db["tenants"].find_one({"slug": "mass-drips"})
    if existing:
        tenant_id = str(existing["_id"])
        print(f"[SKIP] Tenant already exists: {tenant_id}")
    else:
        result = await db["tenants"].insert_one(MASS_DRIPS_TENANT.copy())
        tenant_id = str(result.inserted_id)
        print(f"[OK]   Tenant created: Mass Drips -> {tenant_id}")

    # ── Leads ──────────────────────────────────────────────────────────────
    count = await db["leads"].count_documents({"tenant_id": tenant_id})
    if count > 0:
        print(f"[SKIP] Leads already seeded ({count} exist)")
    else:
        for lead in SAMPLE_LEADS:
            doc = {**lead, "tenant_id": tenant_id, "created_at": NOW, "updated_at": NOW}
            r = await db["leads"].insert_one(doc)
            print(f"[OK]   Lead: {lead['name']} -> {r.inserted_id}")

    # ── Products ───────────────────────────────────────────────────────────
    count = await db["products"].count_documents({"tenant_id": tenant_id})
    if count > 0:
        print(f"[SKIP] Products already seeded ({count} exist)")
    else:
        for product in MASS_DRIPS_PRODUCTS:
            doc = {**product, "tenant_id": tenant_id, "created_at": NOW, "updated_at": NOW}
            r = await db["products"].insert_one(doc)
            print(f"[OK]   Product: {product['name']} -> {r.inserted_id}")

    # ── MongoDB Indexes ────────────────────────────────────────────────────
    await db["tenants"].create_index("slug", unique=True, background=True)
    await db["leads"].create_index([("tenant_id", 1), ("status", 1)], background=True)
    await db["leads"].create_index("phone", background=True)
    await db["products"].create_index([("tenant_id", 1), ("in_stock", 1)], background=True)
    await db["calls"].create_index([("tenant_id", 1), ("lead_id", 1)], background=True)
    print("[OK]   MongoDB indexes created")

    print("\n=== Seeding complete! ===")
    print(f"Tenant ID : {tenant_id}")
    print(f"Test WS   : ws://localhost:8000/ws/voice/{tenant_id}/<lead_id>")
    print(f"Docs URL  : http://localhost:8000/docs")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
