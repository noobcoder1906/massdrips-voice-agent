import asyncio
import os
import requests
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def sync_massdrips_catalog():
    print("="*50)
    print("Mass Drips Catalog Auto-Sync (Cron Job)")
    print("="*50)

    # 1. Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("ERROR: MONGO_URI not found in .env")
        return
        
    client = AsyncIOMotorClient(mongo_uri)
    db = client[os.getenv("DB_NAME", "voxsales")]
    
    # Get the Mass Drips tenant ID
    tenant = await db["tenants"].find_one({"slug": "mass-drips"})
    if not tenant:
        print("ERROR: Mass Drips tenant not found. Run seed_db.py first.")
        return
    tenant_id = str(tenant["_id"])
    
    # 2. Scrape the live website
    url = "https://massdrips.shop/shop"
    headers = {'User-Agent': 'Mozilla/5.0'}
    print(f"Scraping {url}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        products = []
        for heading in soup.find_all(['h2', 'h3']):
            title = heading.text.strip()
            if title and len(title) > 3:
                # We assume a default price if not found on the page layout
                products.append({
                    "name": title,
                    "price": 1499.0, # Defaulting for now
                    "currency": "INR",
                    "in_stock": True,
                    "tenant_id": tenant_id
                })
                
        print(f"Found {len(products)} products on the live site.")
        
        # 3. Update MongoDB (Upsert logic to avoid duplicates)
        updated_count = 0
        new_count = 0
        
        for p in products:
            existing = await db["products"].find_one({"name": p["name"], "tenant_id": tenant_id})
            if existing:
                await db["products"].update_one(
                    {"_id": existing["_id"]}, 
                    {"$set": {"in_stock": True, "price": p["price"]}}
                )
                updated_count += 1
            else:
                await db["products"].insert_one(p)
                new_count += 1
                
        print(f"Sync Complete! Added {new_count} new products. Updated {updated_count} existing products.")
        
    except Exception as e:
        print(f"Failed to scrape or sync: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(sync_massdrips_catalog())
