import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0'}

def get_page(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8', errors='ignore')

# 1. Fetch main page
html = get_page('https://www.massdrips.shop/')

# Find all JS bundle links
js_urls = list(set(re.findall(r'src=["\'](/assets/[^"\']+\.js)["\']', html) + re.findall(r'href=["\'](/assets/[^"\']+\.js)["\']', html)))
print(f"Found {len(js_urls)} JS files to inspect")

all_products = []

for path in js_urls:
    full_url = 'https://www.massdrips.shop' + path
    try:
        content = get_page(full_url)
        # Search for product object shapes
        # e.g., id:"MD...", name:"...", price:..., collection:"..."
        matches = re.finditer(r'id:\s*["\'](MD\d+)["\'],(?:slug:\s*["\']([^"\']+)["\'],)?name:\s*["\']([^"\']+)["\'],category:\s*["\']([^"\']+)["\'],price:\s*(\d+)', content)
        for m in matches:
            all_products.append({
                'id': m.group(1),
                'slug': m.group(2) or '',
                'name': m.group(3),
                'category': m.group(4),
                'price': int(m.group(5)),
            })
        
        # General pattern
        gen_matches = re.finditer(r'\{id:\s*["\'](MD\d+)["\'],name:\s*["\']([^"\']+)["\'],price:\s*(\d+)', content)
        for gm in gen_matches:
            if not any(p['id'] == gm.group(1) for p in all_products):
                all_products.append({
                    'id': gm.group(1),
                    'name': gm.group(2),
                    'price': int(gm.group(3)),
                    'category': 'Streetwear Drop'
                })
    except Exception as e:
        print(f"Error fetching {full_url}: {e}")

print(f"Total scraped live products: {len(all_products)}")
for p in all_products:
    print(f"  • [{p['id']}] {p['name']} — ₹{p['price']} ({p.get('category', 'Streetwear')})")

with open('backend/services/scraped_site_data.json', 'w', encoding='utf-8') as f:
    json.dump({
        'brand': 'MASS DRIPS',
        'website': 'https://www.massdrips.shop/',
        'tagline': 'Wear The Mass | Cinematic Streetwear',
        'origin': 'Made in Chennai, India',
        'fabric': '240 GSM Heavyweight Premium French Terry & Cotton',
        'shipping': '3-4 Days Pan-India Delivery',
        'payment': 'COD (Cash on Delivery) + UPI',
        'collections': [
            {'name': 'Kollywood', 'styles': 15, 'fromPrice': 699, 'desc': 'Tamil cinema mass icons & cult dialogues'},
            {'name': 'Bollywood', 'styles': 5, 'fromPrice': 699, 'desc': 'Hindi cinema legends & cult classics'},
            {'name': 'Tollywood', 'styles': 3, 'fromPrice': 699, 'desc': 'Telugu cinema hero statements'},
            {'name': 'Love Edition', 'styles': 2, 'fromPrice': 799, 'desc': 'Romance & aesthetic cinematic pieces'},
            {'name': 'Mass Edition', 'styles': 1, 'fromPrice': 1499, 'desc': 'Flagship signature drops'},
            {'name': 'Heavyweights', 'styles': 4, 'fromPrice': 1499, 'desc': '240 GSM oversized hoodies & sweatshirts'}
        ],
        'products': all_products if all_products else [
            {'id': 'MD001', 'name': 'Jana Nayagan — Crowd Edition', 'price': 699, 'category': 'Premium Oversized Tee', 'color': 'Black', 'gsm': '240 GSM', 'badge': 'HOT'},
            {'id': 'MD002', 'name': 'In The Shadows We Forge', 'price': 1499, 'category': 'Oversized Hoodie', 'color': 'Black', 'gsm': '240 GSM', 'badge': 'BESTSELLER'},
            {'id': 'MD003', 'name': 'Main Rukta Nahi Hoon', 'price': 1199, 'category': 'Sweatshirt', 'color': 'Black', 'gsm': '240 GSM', 'badge': 'NEW'},
            {'id': 'MD004', 'name': 'Main Rukta Nahi Hoon', 'price': 699, 'category': 'Oversized Tee', 'color': 'Black', 'gsm': '240 GSM', 'badge': 'TRENDING'},
            {'id': 'MD005', 'name': 'Kismat Der Se Aye', 'price': 699, 'category': 'Cracked Wall Tee', 'color': 'Black', 'gsm': '240 GSM', 'badge': 'TRENDING'},
            {'id': 'MD006', 'name': 'Kismat Der Se Aye', 'price': 1599, 'category': 'Cracked Hoodie — Melange Grey', 'color': 'Melange Grey', 'gsm': '240 GSM', 'badge': 'NEW'},
            {'id': 'MD007', 'name': 'Kismat Der Se Aye', 'price': 1599, 'category': 'Cracked Hoodie — White', 'color': 'White', 'gsm': '240 GSM', 'badge': 'HOT'},
        ]
    }, f, indent=2)

