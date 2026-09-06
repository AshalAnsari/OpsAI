"""
Backfill product image_urls + specs for an already-seeded database.

Usage (from backend container or local with DATABASE_URL):
    python -m scripts.backfill_product_images
"""

from __future__ import annotations

import json

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.product import Product

# Curated Unsplash images matched to each fictional OpsPilot product.
# Multiple URLs enable the product detail carousel.
PRODUCT_MEDIA: dict[str, dict] = {
    "Nimbus Cloud Desk": {
        "image_urls": [
            "https://images.unsplash.com/photo-1593062096033-9a26b09da705?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Material": "Oak + steel", "Height range": "70–120 cm", "Finish": "Matte"},
    },
    "Orbit Focus Lamp": {
        "image_urls": [
            "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1543198126-a8ad8e47fb22?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Power": "12W", "Color temp": "2700–6500K", "Mount": "Desk clamp"},
    },
    "Helix Cable Hub": {
        "image_urls": [
            "https://images.unsplash.com/photo-1625948515291-69613efd103f?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Ports": "6", "PD": "65W", "Cable length": "1.5m"},
    },
    "Aether Noise Canceller": {
        "image_urls": [
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Panels": "4", "NRC": "0.85", "Mount": "Freestanding"},
    },
    "Pulse Status Beacon": {
        "image_urls": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1518444065439-e933c06ce9cd?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Connectivity": "BLE", "Battery": "30 days", "Modes": "4 colors"},
    },
    "Quill Ops Notebook": {
        "image_urls": [
            "https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Pages": "192", "Size": "A5", "Paper": "Dotted 100gsm"},
    },
    "Forge Tool Roll": {
        "image_urls": [
            "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1530124566582-a618bc2610dc?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Pockets": "12", "Material": "Waxed canvas", "Weight": "480g"},
    },
    "Cascade Monitor Arm": {
        "image_urls": [
            "https://images.unsplash.com/photo-1527443195645-1133f7f28908?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Screens": '2x32"', "VESA": "75/100", "Clamp": "Desk + grommet"},
    },
    "Zenith Ergonomic Chair": {
        "image_urls": [
            "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Weight capacity": "140kg", "Warranty": "5 years", "Lumbar": "Adjustable"},
    },
    "Lumen Keyboard": {
        "image_urls": [
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1618384887929-16ec33cab9ef?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Switches": "Silent linear", "Layout": "75%", "Connection": "USB-C / BT"},
    },
    "Drift Wireless Mouse": {
        "image_urls": [
            "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1605773527852-c546a8584ea3?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"DPI": "4000", "Battery": "70 days", "Buttons": "6"},
    },
    "Summit Laptop Stand": {
        "image_urls": [
            "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1484788984921-03950022c9ef?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Angle": "15°", "Material": "Aluminum", "Fit": "11–16 inch"},
    },
    "Harbor Dock Station": {
        "image_urls": [
            "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1625948515291-69613efd103f?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Ports": "12", "Video": "Dual 4K", "Power": "96W pass-through"},
    },
    "Relay Badge Holder": {
        "image_urls": [
            "https://images.unsplash.com/photo-1586953208448-b95a79798f07?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1606761568499-6d2451b23c66?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Material": "Recycled PET", "NFC": "Yes", "Color": "Slate"},
    },
    "Atlas Wall Map": {
        "image_urls": [
            "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
        ],
        "specs": {"Size": '24x36"', "Finish": "Matte", "Paper": "Archival"},
    },
}


def backfill() -> None:
    db = SessionLocal()
    try:
        products = list(db.scalars(select(Product)))
        updated = 0
        for product in products:
            media = PRODUCT_MEDIA.get(product.name)
            if not media:
                print(f"Skip (no mapping): {product.name}")
                continue
            product.image_urls = media["image_urls"]
            if not product.specs:
                product.specs = media["specs"]
            db.add(product)
            updated += 1
            print(f"Updated: {product.name} ({len(media['image_urls'])} images)")
        db.commit()
        print(json.dumps({"updated": updated, "total": len(products)}))
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
