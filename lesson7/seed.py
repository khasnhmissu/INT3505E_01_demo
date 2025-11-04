# seed.py
"""
Script để xóa và thêm dữ liệu mẫu vào MongoDB
Chạy: python seed.py
"""
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["shop_manager"]

print("=" * 60)
print("🌱 SEEDING DATABASE: shop_manager")
print("=" * 60)

# ========================================
# 1. XÓA DỮ LIỆU CŨ
# ========================================
print("\n🗑️  Đang xóa dữ liệu cũ...")
db.products.delete_many({})
db.customers.delete_many({})
db.orders.delete_many({})
print("✅ Đã xóa tất cả dữ liệu cũ")

# ========================================
# 2. THÊM PRODUCTS
# ========================================
print("\n📦 Đang thêm products...")
products = [
    {
        "name": "Laptop Dell XPS 13",
        "price": 1299.99,
        "stock": 15,
        "category": "Electronics"
    },
    {
        "name": "iPhone 15 Pro",
        "price": 999.99,
        "stock": 25,
        "category": "Electronics"
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "price": 399.99,
        "stock": 30,
        "category": "Audio"
    },
    {
        "name": "Mechanical Keyboard Keychron K2",
        "price": 89.99,
        "stock": 50,
        "category": "Accessories"
    }
]

product_result = db.products.insert_many(products)
product_ids = product_result.inserted_ids
print(f"✅ Đã thêm {len(product_ids)} products")
for i, pid in enumerate(product_ids):
    print(f"   - {products[i]['name']}: {pid}")

# ========================================
# 3. THÊM CUSTOMERS
# ========================================
print("\n👥 Đang thêm customers...")
customers = [
    {
        "name": "Nguyễn Văn An",
        "email": "nguyen.van.an@email.com",
        "phone": "0901234567",
        "address": "123 Đường Lê Lợi, Quận 1, TP.HCM"
    },
    {
        "name": "Trần Thị Bình",
        "email": "tran.thi.binh@email.com",
        "phone": "0912345678",
        "address": "456 Đường Nguyễn Huệ, Quận 1, TP.HCM"
    },
    {
        "name": "Lê Hoàng Cường",
        "email": "le.hoang.cuong@email.com",
        "phone": "0923456789",
        "address": "789 Đường Hai Bà Trưng, Quận 3, TP.HCM"
    }
]

customer_result = db.customers.insert_many(customers)
customer_ids = customer_result.inserted_ids
print(f"✅ Đã thêm {len(customer_ids)} customers")
for i, cid in enumerate(customer_ids):
    print(f"   - {customers[i]['name']}: {cid}")

# ========================================
# 4. THÊM ORDERS
# ========================================
print("\n📋 Đang thêm orders...")

# Order 1: Customer 0 mua Product 0 và Product 2
order1_products = [product_ids[0], product_ids[2]]
order1_total = products[0]['price'] + products[2]['price']
order1 = {
    "customer_id": customer_ids[0],
    "product_ids": order1_products,
    "total_price": order1_total,
    "status": "delivered",
    "notes": "Giao hàng nhanh",
    "created_at": datetime(2024, 10, 15, 10, 30, 0),
    "updated_at": datetime(2024, 10, 18, 14, 0, 0)
}

# Order 2: Customer 1 mua Product 1
order2_products = [product_ids[1]]
order2_total = products[1]['price']
order2 = {
    "customer_id": customer_ids[1],
    "product_ids": order2_products,
    "total_price": order2_total,
    "status": "shipped",
    "notes": "",
    "created_at": datetime(2024, 10, 20, 9, 15, 0),
    "updated_at": datetime(2024, 10, 22, 16, 30, 0)
}

# Order 3: Customer 2 mua Product 1, Product 2, và Product 3
order3_products = [product_ids[1], product_ids[2], product_ids[3]]
order3_total = products[1]['price'] + products[2]['price'] + products[3]['price']
order3 = {
    "customer_id": customer_ids[2],
    "product_ids": order3_products,
    "total_price": order3_total,
    "status": "pending",
    "notes": "Khách hàng VIP",
    "created_at": datetime.utcnow()
}

orders = [order1, order2, order3]
order_result = db.orders.insert_many(orders)
order_ids = order_result.inserted_ids
print(f"✅ Đã thêm {len(order_ids)} orders")
for i, oid in enumerate(order_ids):
    print(f"   - Order {i+1} (Customer: {customers[i]['name']}): {oid}")

# ========================================
# 5. THỐNG KÊ
# ========================================
print("📊 THỐNG KÊ DATABASE")
print(f"📦 Products: {db.products.count_documents({})}")
print(f"👥 Customers: {db.customers.count_documents({})}")
print(f"📋 Orders: {db.orders.count_documents({})}")
print("\n✅ DATABASE SEEDED SUCCESSFULLY!")

# Đóng kết nối
client.close()