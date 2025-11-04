# app/products_routes.py
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from bson.errors import InvalidId
from routes import mongo

# Tạo Blueprint cho Products
products_bp = Blueprint('products', __name__)

# ========================================
# HELPER FUNCTIONS
# ========================================
def serialize_product(product):
    """Chuyển ObjectId sang string"""
    if product and '_id' in product:
        product['_id'] = str(product['_id'])
    return product

def serialize_products(products):
    """Chuyển danh sách products"""
    return [serialize_product(p) for p in products]

# ========================================
# CRUD ENDPOINTS
# ========================================

@products_bp.route('/products', methods=['GET'])
def get_all_products():
    """Lấy tất cả products"""
    try:
        products = list(mongo.db.products.find())
        products = serialize_products(products)
        
        return jsonify({
            "success": True,
            "data": products,
            "total": len(products)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@products_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Lấy 1 product theo ID"""
    try:
        obj_id = ObjectId(product_id)
        product = mongo.db.products.find_one({"_id": obj_id})
        
        if not product:
            return jsonify({
                "success": False,
                "message": f"Product {product_id} không tồn tại"
            }), 404
        
        product = serialize_product(product)
        return jsonify({
            "success": True,
            "data": product
        }), 200
        
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "ID không hợp lệ"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@products_bp.route('/products', methods=['POST'])
def create_product():
    """Tạo product mới"""
    try:
        data = request.get_json()
        
        # Validate
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({
                "success": False,
                "message": "Thiếu 'name' hoặc 'price'"
            }), 400
        
        # Tạo document
        new_product = {
            "name": data['name'],
            "price": float(data['price']),
            "stock": data.get('stock', 0),
            "category": data.get('category', 'General')
        }
        
        result = mongo.db.products.insert_one(new_product)
        new_product['_id'] = str(result.inserted_id)
        
        return jsonify({
            "success": True,
            "message": "Tạo product thành công",
            "data": new_product
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@products_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Cập nhật product"""
    try:
        obj_id = ObjectId(product_id)
        
        # Kiểm tra tồn tại
        if not mongo.db.products.find_one({"_id": obj_id}):
            return jsonify({
                "success": False,
                "message": f"Product {product_id} không tồn tại"
            }), 404
        
        data = request.get_json()
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'price' in data:
            update_data['price'] = float(data['price'])
        if 'stock' in data:
            update_data['stock'] = data['stock']
        if 'category' in data:
            update_data['category'] = data['category']
        
        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu để cập nhật"
            }), 400
        
        mongo.db.products.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        updated = mongo.db.products.find_one({"_id": obj_id})
        updated = serialize_product(updated)
        
        return jsonify({
            "success": True,
            "message": "Cập nhật thành công",
            "data": updated
        }), 200
        
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "ID không hợp lệ"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@products_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Xóa product"""
    try:
        obj_id = ObjectId(product_id)
        
        # Kiểm tra tồn tại
        if not mongo.db.products.find_one({"_id": obj_id}):
            return jsonify({
                "success": False,
                "message": f"Product {product_id} không tồn tại"
            }), 404
        
        result = mongo.db.products.delete_one({"_id": obj_id})
        
        return jsonify({
            "success": True,
            "message": "Xóa thành công",
            "deleted_count": result.deleted_count
        }), 200
        
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "ID không hợp lệ"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500