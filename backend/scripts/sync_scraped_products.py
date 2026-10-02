import asyncio
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.database import connect_to_mongo, get_db, close_mongo_connection

async def main():
    await connect_to_mongo()
    db = get_db()
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", "scraped_site_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        site_data = json.load(f)
    
    prods = site_data.get("products", [])
    for p in prods:
        doc = {
            "tenant_id": "tenant_123",
            "product_id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "category": p["category"],
            "gsm": p.get("gsm", "240 GSM"),
            "badge": p.get("badge", ""),
            "color": p.get("color", "Black"),
            "description": f"{p.get('gsm', '240 GSM')} {p.get('category')} graphic piece in {p.get('color', 'Black')}.",
            "in_stock": True,
        }
        await db["products"].update_one(
            {"tenant_id": "tenant_123", "name": p["name"]},
            {"$set": doc},
            upsert=True
        )
    print(f"Successfully upserted {len(prods)} products for tenant_123 in MongoDB!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
