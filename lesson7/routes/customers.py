# app/customers_routes.py
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from bson.errors import InvalidId
from routes import mongo

# Tạo Blueprint cho Customers
customers_bp = Blueprint('customers', __name__)

# ========================================
# HELPER FUNCTIONS
# ========================================
def serialize_customer(customer):
    """Chuyển ObjectId sang string"""
    if customer and '_id' in customer:
        customer['_id'] = str(customer['_id'])
    return customer

def serialize_customers(customers):
    """Chuyển danh sách customers"""
    return [serialize_customer(c) for c in customers]

# ========================================
# CRUD ENDPOINTS
# ========================================

@customers_bp.route('/customers', methods=['GET'])
def get_all_customers():
    """Lấy tất cả customers"""
    try:
        customers = list(mongo.db.customers.find())
        customers = serialize_customers(customers)
        
        return jsonify({
            "success": True,
            "data": customers,
            "total": len(customers)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@customers_bp.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Lấy 1 customer theo ID"""
    try:
        obj_id = ObjectId(customer_id)
        customer = mongo.db.customers.find_one({"_id": obj_id})
        
        if not customer:
            return jsonify({
                "success": False,
                "message": f"Customer {customer_id} không tồn tại"
            }), 404
        
        customer = serialize_customer(customer)
        return jsonify({
            "success": True,
            "data": customer
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

@customers_bp.route('/customers', methods=['POST'])
def create_customer():
    """Tạo customer mới"""
    try:
        data = request.get_json()
        
        # Validate
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Thiếu trường '{field}'"
                }), 400
        
        # Kiểm tra email trùng
        existing = mongo.db.customers.find_one({"email": data['email']})
        if existing:
            return jsonify({
                "success": False,
                "message": f"Email '{data['email']}' đã tồn tại"
            }), 400
        
        # Tạo document
        new_customer = {
            "name": data['name'],
            "email": data['email'],
            "phone": data.get('phone', ''),
            "address": data.get('address', '')
        }
        
        result = mongo.db.customers.insert_one(new_customer)
        new_customer['_id'] = str(result.inserted_id)
        
        return jsonify({
            "success": True,
            "message": "Tạo customer thành công",
            "data": new_customer
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@customers_bp.route('/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Cập nhật customer"""
    try:
        obj_id = ObjectId(customer_id)
        
        # Kiểm tra tồn tại
        if not mongo.db.customers.find_one({"_id": obj_id}):
            return jsonify({
                "success": False,
                "message": f"Customer {customer_id} không tồn tại"
            }), 404
        
        data = request.get_json()
        update_data = {}
        
        # Kiểm tra email trùng (nếu cập nhật email)
        if 'email' in data:
            existing = mongo.db.customers.find_one({
                "email": data['email'],
                "_id": {"$ne": obj_id}
            })
            if existing:
                return jsonify({
                    "success": False,
                    "message": f"Email '{data['email']}' đã được sử dụng"
                }), 400
            update_data['email'] = data['email']
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'address' in data:
            update_data['address'] = data['address']
        
        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu để cập nhật"
            }), 400
        
        mongo.db.customers.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        updated = mongo.db.customers.find_one({"_id": obj_id})
        updated = serialize_customer(updated)
        
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

@customers_bp.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Xóa customer"""
    try:
        obj_id = ObjectId(customer_id)
        
        # Kiểm tra tồn tại
        if not mongo.db.customers.find_one({"_id": obj_id}):
            return jsonify({
                "success": False,
                "message": f"Customer {customer_id} không tồn tại"
            }), 404
        
        # Kiểm tra xem customer có orders không
        orders_count = mongo.db.orders.count_documents({"customer_id": obj_id})
        if orders_count > 0:
            return jsonify({
                "success": False,
                "message": f"Không thể xóa customer. Còn {orders_count} orders liên quan."
            }), 400
        
        result = mongo.db.customers.delete_one({"_id": obj_id})
        
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