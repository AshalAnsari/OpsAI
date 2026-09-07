"""
Seed Harbor Dock Station with fictional demo data.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import random
from decimal import Decimal

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.role import Role, User
from app.services.fulfillment_service import location_for_status
from app.services.product_service import slugify

settings = get_settings()

PRODUCTS = [
    ("Nimbus Cloud Desk", "Modular standing desk for hybrid ops teams.", Decimal("449.00"), 40, [
        "https://images.unsplash.com/photo-1593062096033-9a26b09da705?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    ], {"Material": "Oak + steel", "Height range": "70–120 cm", "Finish": "Matte"}),
    ("Orbit Focus Lamp", "Adjustable LED lamp with circadian modes.", Decimal("89.00"), 120, [
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1543198126-a8ad8e47fb22?auto=format&fit=crop&w=1200&q=80",
    ], {"Power": "12W", "Color temp": "2700–6500K", "Mount": "Desk clamp"}),
    ("Helix Cable Hub", "Desk cable management hub with USB-C PD.", Decimal("59.00"), 200, [
        "https://images.unsplash.com/photo-1625948515291-69613efd103f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1200&q=80",
    ], {"Ports": "6", "PD": "65W", "Cable length": "1.5m"}),
    ("Aether Noise Canceller", "Desktop acoustic panel kit.", Decimal("129.00"), 75, [
        "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    ], {"Panels": "4", "NRC": "0.85", "Mount": "Freestanding"}),
    ("Pulse Status Beacon", "Team availability desk beacon.", Decimal("39.00"), 150, [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518444065439-e933c06ce9cd?auto=format&fit=crop&w=1200&q=80",
    ], {"Connectivity": "BLE", "Battery": "30 days", "Modes": "4 colors"}),
    ("Quill Ops Notebook", "Dotted field notebook for runbooks.", Decimal("18.00"), 300, [
        "https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=1200&q=80",
    ], {"Pages": "192", "Size": "A5", "Paper": "Dotted 100gsm"}),
    ("Forge Tool Roll", "Canvas roll for field technicians.", Decimal("74.00"), 90, [
        "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1530124566582-a618bc2610dc?auto=format&fit=crop&w=1200&q=80",
    ], {"Pockets": "12", "Material": "Waxed canvas", "Weight": "480g"}),
    ("Cascade Monitor Arm", "Dual-monitor spring arm.", Decimal("199.00"), 55, [
        "https://images.unsplash.com/photo-1527443195645-1133f7f28908?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=1200&q=80",
    ], {"Screens": "2x32\"", "VESA": "75/100", "Clamp": "Desk + grommet"}),
    ("Zenith Ergonomic Chair", "Mesh chair tuned for long ops shifts.", Decimal("529.00"), 35, [
        "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&w=1200&q=80",
    ], {"Weight capacity": "140kg", "Warranty": "5 years", "Lumbar": "Adjustable"}),
    ("Lumen Keyboard", "Low-profile mechanical keyboard.", Decimal("149.00"), 80, [
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1618384887929-16ec33cab9ef?auto=format&fit=crop&w=1200&q=80",
    ], {"Switches": "Silent linear", "Layout": "75%", "Connection": "USB-C / BT"}),
    ("Drift Wireless Mouse", "Silent click mouse for shared spaces.", Decimal("49.00"), 160, [
        "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1605773527852-c546a8584ea3?auto=format&fit=crop&w=1200&q=80",
    ], {"DPI": "4000", "Battery": "70 days", "Buttons": "6"}),
    ("Summit Laptop Stand", "Aluminum stand with airflow channels.", Decimal("69.00"), 110, [
        "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1484788984921-03950022c9ef?auto=format&fit=crop&w=1200&q=80",
    ], {"Angle": "15°", "Material": "Aluminum", "Fit": "11–16 inch"}),
    ("Harbor Dock Station", "Thunderbolt dock for docking pods.", Decimal("249.00"), 45, [
        "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1625948515291-69613efd103f?auto=format&fit=crop&w=1200&q=80",
    ], {"Ports": "12", "Video": "Dual 4K", "Power": "96W pass-through"}),
    ("Relay Badge Holder", "NFC-ready staff badge sleeve.", Decimal("12.00"), 400, [
        "https://images.unsplash.com/photo-1586953208448-b95a79798f07?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1606761568499-6d2451b23c66?auto=format&fit=crop&w=1200&q=80",
    ], {"Material": "Recycled PET", "NFC": "Yes", "Color": "Slate"}),
    ("Atlas Wall Map", "Fictional ops region wall map print.", Decimal("34.00"), 95, [
        "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
    ], {"Size": "24x36\"", "Finish": "Matte", "Paper": "Archival"}),
]

CUSTOMERS = [
    ("Ava", "North", "ava.north@harbordock.demo"),
    ("Ben", "Harbor", "ben.harbor@harbordock.demo"),
    ("Cora", "Quill", "cora.quill@harbordock.demo"),
    ("Diego", "Forge", "diego.forge@harbordock.demo"),
    ("Elena", "Summit", "elena.summit@harbordock.demo"),
    ("Finn", "Cascade", "finn.cascade@harbordock.demo"),
    ("Gina", "Orbit", "gina.orbit@harbordock.demo"),
    ("Hugo", "Lumen", "hugo.lumen@harbordock.demo"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Role).count() > 0:
            print("Database already seeded. Skipping.")
            return

        admin_role = Role(name="admin")
        customer_role = Role(name="customer")
        db.add_all([admin_role, customer_role])
        db.flush()

        admin = User(
            email=settings.seed_admin_email,
            password_hash=hash_password(settings.seed_admin_password),
            first_name="Ops",
            last_name="Admin",
            is_active=True,
            roles=[admin_role],
        )
        db.add(admin)
        db.flush()

        customers: list[User] = []
        for first, last, email in CUSTOMERS:
            user = User(
                email=email,
                password_hash=hash_password(settings.seed_customer_password),
                first_name=first,
                last_name=last,
                is_active=True,
                roles=[customer_role],
            )
            customers.append(user)
            db.add(user)
        db.flush()

        products: list[Product] = []
        for name, description, price, stock, images, specs in PRODUCTS:
            product = Product(
                name=name,
                slug=slugify(name),
                description=description,
                price=price,
                stock_quantity=stock,
                is_active=True,
                image_urls=images,
                specs=specs,
            )
            products.append(product)
            db.add(product)
        db.flush()

        statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.DISPATCHED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.IN_TRANSIT_INTERNATIONAL,
            OrderStatus.CUSTOMS_CLEARANCE,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ]
        shipping_destinations = [
            ("US", "United States"),
            ("US", "United States"),
            ("CA", "Canada"),
            ("GB", "United Kingdom"),
            ("DE", "Germany"),
            ("AU", "Australia"),
        ]

        for i in range(15):
            customer = random.choice(customers)
            selected = random.sample(products, k=random.randint(1, 3))
            items: list[OrderItem] = []
            total = Decimal("0.00")
            for product in selected:
                qty = random.randint(1, 2)
                unit = Decimal(product.price)
                subtotal = unit * qty
                total += subtotal
                items.append(
                    OrderItem(
                        product_id=product.id,
                        quantity=qty,
                        unit_price=unit,
                        subtotal=subtotal,
                    )
                )
                if statuses[i % len(statuses)] != OrderStatus.CANCELLED:
                    product.stock_quantity = max(0, product.stock_quantity - qty)

            status = statuses[i % len(statuses)]
            # International-only statuses use a non-US destination.
            if status in {
                OrderStatus.IN_TRANSIT_INTERNATIONAL,
                OrderStatus.CUSTOMS_CLEARANCE,
            }:
                country_code, country_name = random.choice(
                    [d for d in shipping_destinations if d[0] != "US"]
                )
            elif status in {OrderStatus.DISPATCHED, OrderStatus.OUT_FOR_DELIVERY} and i % 2:
                country_code, country_name = ("US", "United States")
            else:
                country_code, country_name = shipping_destinations[i % len(shipping_destinations)]

            payment = (
                PaymentStatus.PAID
                if status not in {OrderStatus.PENDING, OrderStatus.CANCELLED}
                else PaymentStatus.PENDING
                if status == OrderStatus.PENDING
                else PaymentStatus.FAILED
            )
            order = Order(
                customer_id=customer.id,
                status=status,
                payment_status=payment,
                total_amount=total,
                shipping_country=country_code,
                shipping_country_name=country_name,
                items=items,
                stripe_checkout_session_id=f"cs_test_seed_{i+1}",
            )
            if payment == PaymentStatus.PAID and status != OrderStatus.CANCELLED:
                order.current_location = location_for_status(order, status)
            db.add(order)

        db.add(
            AuditLog(
                user_id=admin.id,
                action="system.seeded",
                entity_type="system",
                entity_id="seed",
                metadata_json={"products": len(products), "customers": len(customers)},
            )
        )
        for user in customers:
            db.add(
                AuditLog(
                    user_id=user.id,
                    action="user.registered",
                    entity_type="user",
                    entity_id=str(user.id),
                    metadata_json={"email": user.email, "seeded": True},
                )
            )

        db.commit()
        print("Seed complete.")
        print(f"  Admin:    {settings.seed_admin_email} / {settings.seed_admin_password}")
        print(f"  Customer: {CUSTOMERS[0][2]} / {settings.seed_customer_password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
