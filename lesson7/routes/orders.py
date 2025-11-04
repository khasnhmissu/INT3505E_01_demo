# app/orders_routes.py
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from bson.errors import InvalidId
from routes import mongo
from datetime import datetime

# Tạo Blueprint cho Orders
orders_bp = Blueprint('orders', __name__)

# ========================================
# HELPER FUNCTIONS
# ========================================
def serialize_order(order):
    """Chuyển ObjectId sang string"""
    if order:
        if '_id' in order:
            order['_id'] = str(order['_id'])
        if 'customer_id' in order:
            order['customer_id'] = str(order['customer_id'])
        if 'product_ids' in order:
            order['product_ids'] = [str(pid) for pid in order['product_ids']]
    return order

def serialize_orders(orders):
    """Chuyển danh sách orders"""
    return [serialize_order(o) for o in orders]

def calculate_total_price(product_ids):
    """Tính tổng giá từ danh sách product IDs"""
    try:
        obj_ids = [ObjectId(pid) for pid in product_ids]
        products = mongo.db.products.find({"_id": {"$in": obj_ids}})
        total = sum(p.get('price', 0) for p in products)
        return total
    except:
        return 0

# ========================================
# CRUD ENDPOINTS
# ========================================

@orders_bp.route('/orders', methods=['GET'])
def get_all_orders():
    """Lấy tất cả orders (có thể kèm thông tin customer và products)"""
    try:
        # Query parameter để expand data
        expand = request.args.get('expand', '').split(',')
        
        orders = list(mongo.db.orders.find())
        
        # Nếu có expand=customer,products thì lookup thông tin
        for order in orders:
            if 'customer' in expand and 'customer_id' in order:
                customer = mongo.db.customers.find_one({"_id": order['customer_id']})
                if customer:
                    order['customer_info'] = {
                        '_id': str(customer['_id']),
                        'name': customer.get('name'),
                        'email': customer.get('email')
                    }
            
            if 'products' in expand and 'product_ids' in order:
                products = list(mongo.db.products.find({
                    "_id": {"$in": order['product_ids']}
                }))
                order['products_info'] = [
                    {
                        '_id': str(p['_id']),
                        'name': p.get('name'),
                        'price': p.get('price')
                    } for p in products
                ]
        
        orders = serialize_orders(orders)
        
        return jsonify({
            "success": True,
            "data": orders,
            "total": len(orders)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@orders_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Lấy 1 order theo ID (kèm thông tin customer và products)"""
    try:
        obj_id = ObjectId(order_id)
        order = mongo.db.orders.find_one({"_id": obj_id})
        
        if not order:
            return jsonify({
                "success": False,
                "message": f"Order {order_id} không tồn tại"
            }), 404
        
        # Lookup customer info
        if 'customer_id' in order:
            customer = mongo.db.customers.find_one({"_id": order['customer_id']})
            if customer:
                order['customer_info'] = {
                    '_id': str(customer['_id']),
                    'name': customer.get('name'),
                    'email': customer.get('email'),
                    'phone': customer.get('phone')
                }
        
        # Lookup products info
        if 'product_ids' in order:
            products = list(mongo.db.products.find({
                "_id": {"$in": order['product_ids']}
            }))
            order['products_info'] = [
                {
                    '_id': str(p['_id']),
                    'name': p.get('name'),
                    'price': p.get('price'),
                    'category': p.get('category')
                } for p in products
            ]
        
        order = serialize_order(order)
        
        return jsonify({
            "success": True,
            "data": order
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

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """Tạo order mới"""
    try:
        data = request.get_json()
        
        # Validate
        required_fields = ['customer_id', 'product_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Thiếu trường '{field}'"
                }), 400
        
        # Validate customer_id
        try:
            customer_id = ObjectId(data['customer_id'])
            if not mongo.db.customers.find_one({"_id": customer_id}):
                return jsonify({
                    "success": False,
                    "message": f"Customer {data['customer_id']} không tồn tại"
                }), 404
        except InvalidId:
            return jsonify({
                "success": False,
                "message": "customer_id không hợp lệ"
            }), 400
        
        # Validate product_ids
        if not isinstance(data['product_ids'], list) or len(data['product_ids']) == 0:
            return jsonify({
                "success": False,
                "message": "product_ids phải là một mảng không rỗng"
            }), 400
        
        try:
            product_ids = [ObjectId(pid) for pid in data['product_ids']]
        except InvalidId:
            return jsonify({
                "success": False,
                "message": "Một hoặc nhiều product_id không hợp lệ"
            }), 400
        
        # Kiểm tra tất cả products có tồn tại không
        existing_products = mongo.db.products.count_documents({
            "_id": {"$in": product_ids}
        })
        if existing_products != len(product_ids):
            return jsonify({
                "success": False,
                "message": "Một hoặc nhiều products không tồn tại"
            }), 404
        
        # Tính total_price
        total_price = calculate_total_price(data['product_ids'])
        
        # Tạo order
        new_order = {
            "customer_id": customer_id,
            "product_ids": product_ids,
            "total_price": total_price,
            "status": data.get('status', 'pending'),
            "created_at": datetime.utcnow(),
            "notes": data.get('notes', '')
        }
        
        result = mongo.db.orders.insert_one(new_order)
        new_order['_id'] = str(result.inserted_id)
        new_order['customer_id'] = str(new_order['customer_id'])
        new_order['product_ids'] = [str(pid) for pid in new_order['product_ids']]
        new_order['created_at'] = new_order['created_at'].isoformat()
        
        return jsonify({
            "success": True,
            "message": "Tạo order thành công",
            "data": new_order
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }), 500

@orders_bp.route('/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    """Cập nhật order (chủ yếu status)"""
    try:
        obj_id = ObjectId(order_id)
        
        # Kiểm tra tồn tại
        existing_order = mongo.db.orders.find_one({"_id": obj_id})
        if not existing_order:
            return jsonify({
                "success": False,
                "message": f"Order {order_id} không tồn tại"
            }), 404
        
        data = request.get_json()
        update_data = {}
        
        # Cho phép cập nhật status và notes
        if 'status' in data:
            allowed_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            if data['status'] not in allowed_statuses:
                return jsonify({
                    "success": False,
                    "message": f"Status phải là một trong: {', '.join(allowed_statuses)}"
                }), 400
            update_data['status'] = data['status']
        
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        # Nếu cập nhật product_ids, tính lại total_price
        if 'product_ids' in data:
            try:
                product_ids = [ObjectId(pid) for pid in data['product_ids']]
                existing_products = mongo.db.products.count_documents({
                    "_id": {"$in": product_ids}
                })
                if existing_products != len(product_ids):
                    return jsonify({
                        "success": False,
                        "message": "Một hoặc nhiều products không tồn tại"
                    }), 404
                
                update_data['product_ids'] = product_ids
                update_data['total_price'] = calculate_total_price(data['product_ids'])
            except InvalidId:
                return jsonify({
                    "success": False,
                    "message": "Một hoặc nhiều product_id không hợp lệ"
                }), 400
        
        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu để cập nhật"
            }), 400
        
        update_data['updated_at'] = datetime.utcnow()
        
        mongo.db.orders.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        updated = mongo.db.orders.find_one({"_id": obj_id})
        updated = serialize_order(updated)
        
        return jsonify({
            "success": True,
            "message": "Cập nhật order thành công",
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

@orders_bp.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Xóa order"""
    try:
        obj_id = ObjectId(order_id)
        
        # Kiểm tra tồn tại
        if not mongo.db.orders.find_one({"_id": obj_id}):
            return jsonify({"success": False,
                "message": f"Order {order_id} không tồn tại"
            }), 404
        
        result = mongo.db.orders.delete_one({"_id": obj_id})
        
        return jsonify({
            "success": True,
            "message": "Xóa order thành công",
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