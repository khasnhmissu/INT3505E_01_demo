# app.py - Phiên bản với MongoDB
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)

# Format: mongodb://[username:password@]host:port/database_name
app.config["MONGO_URI"] = "mongodb://localhost:27017/store_demo"

# Khởi tạo PyMongo
mongo = PyMongo(app)

# Truy cập collection 'products' trong database 'store_demo'
# Collection sẽ tự động được tạo khi insert document đầu tiên
products_collection = mongo.db.products


def serialize_product(product):
    """
    Chuyển đổi _id từ ObjectId sang string để có thể JSON serialize
    MongoDB lưu _id dưới dạng ObjectId, nhưng JSON không hiểu kiểu này
    """
    if product and '_id' in product:
        product['_id'] = str(product['_id'])
    return product


def serialize_products(products):
    """Chuyển đổi danh sách products"""
    return [serialize_product(product) for product in products]


@app.route('/products', methods=['GET'])
def get_all_products():
    """
    Lấy danh sách tất cả products từ MongoDB
    Method: GET
    URL: http://localhost:5000/products
    """
    try:
        # Lấy tất cả documents từ collection 'products'
        # find() trả về cursor (giống iterator)
        products = list(products_collection.find())
        
        # Chuyển đổi ObjectId sang string
        products = serialize_products(products)
        
        return jsonify({
            "success": True,
            "data": products,
            "total": len(products)
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi lấy danh sách products: {str(e)}"
        }), 500


@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """
    Lấy thông tin 1 product theo ID
    Method: GET
    URL: http://localhost:5000/products/507f1f77bcf86cd799439011
    
    Lưu ý: product_id phải là ObjectId hợp lệ (24 ký tự hex)
    """
    try:
        # Chuyển đổi string ID sang ObjectId
        obj_id = ObjectId(product_id)
        
        # Tìm document theo _id
        product = products_collection.find_one({"_id": obj_id})
        
        if product is None:
            return jsonify({
                "success": False,
                "message": f"Product với ID {product_id} không tồn tại"
            }), 404
        
        # Chuyển đổi ObjectId sang string
        product = serialize_product(product)
        
        return jsonify({
            "success": True,
            "data": product
        }), 200
    
    except InvalidId:
        return jsonify({
            "success": False,
            "message": f"ID '{product_id}' không hợp lệ. ID phải là chuỗi 24 ký tự hex."
        }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi lấy product: {str(e)}"
        }), 500


@app.route('/products', methods=['POST'])
def create_product():
    """
    Tạo product mới trong MongoDB
    Method: POST
    URL: http://localhost:5000/products
    Body (JSON):
    {
        "name": "Tên sản phẩm",
        "price": 100,
        "stock": 20
    }
    """
    try:
        # Lấy dữ liệu JSON từ request
        data = request.get_json()
        
        # Kiểm tra dữ liệu đầu vào
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({
                "success": False,
                "message": "Thiếu thông tin 'name' hoặc 'price'"
            }), 400
        
        # Tạo document mới (không cần thêm _id, MongoDB tự tạo)
        new_product = {
            "name": data['name'],
            "price": data['price'],
            "stock": data.get('stock', 0)  # Mặc định stock = 0
        }
        
        # Insert vào MongoDB
        result = products_collection.insert_one(new_product)
        
        # Lấy ID vừa được tạo
        new_product['_id'] = str(result.inserted_id)
        
        return jsonify({
            "success": True,
            "message": "Tạo product thành công",
            "data": new_product
        }), 201  # 201 = Created
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi tạo product: {str(e)}"
        }), 500


@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Cập nhật thông tin product trong MongoDB
    Method: PUT
    URL: http://localhost:5000/products/507f1f77bcf86cd799439011
    Body (JSON):
    {
        "name": "Tên mới",
        "price": 150,
        "stock": 25
    }
    """
    try:
        # Chuyển đổi string ID sang ObjectId
        obj_id = ObjectId(product_id)
        
        # Kiểm tra product có tồn tại không
        existing_product = products_collection.find_one({"_id": obj_id})
        if existing_product is None:
            return jsonify({
                "success": False,
                "message": f"Product với ID {product_id} không tồn tại"
            }), 404
        
        # Lấy dữ liệu cập nhật
        data = request.get_json()
        
        # Tạo dict chứa các field cần update
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'price' in data:
            update_data['price'] = data['price']
        if 'stock' in data:
            update_data['stock'] = data['stock']
        
        # Nếu không có gì để update
        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu để cập nhật"
            }), 400
        
        # Update document trong MongoDB
        products_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        # Lấy product đã được cập nhật
        updated_product = products_collection.find_one({"_id": obj_id})
        updated_product = serialize_product(updated_product)
        
        return jsonify({
            "success": True,
            "message": "Cập nhật product thành công",
            "data": updated_product
        }), 200
    
    except InvalidId:
        return jsonify({
            "success": False,
            "message": f"ID '{product_id}' không hợp lệ"
        }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi cập nhật product: {str(e)}"
        }), 500


@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Xóa product khỏi MongoDB
    Method: DELETE
    URL: http://localhost:5000/products/507f1f77bcf86cd799439011
    """
    try:
        # Chuyển đổi string ID sang ObjectId
        obj_id = ObjectId(product_id)
        
        # Kiểm tra product có tồn tại không
        existing_product = products_collection.find_one({"_id": obj_id})
        if existing_product is None:
            return jsonify({
                "success": False,
                "message": f"Product với ID {product_id} không tồn tại"
            }), 404
        
        # Xóa document khỏi MongoDB
        result = products_collection.delete_one({"_id": obj_id})
        
        return jsonify({
            "success": True,
            "message": f"Đã xóa product ID {product_id}",
            "deleted_count": result.deleted_count
        }), 200
    
    except InvalidId:
        return jsonify({
            "success": False,
            "message": f"ID '{product_id}' không hợp lệ"
        }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi xóa product: {str(e)}"
        }), 500


@app.route('/', methods=['GET'])
def home():
    """Trang chủ API"""
    return jsonify({
        "message": "🚀 Product API - Flask + MongoDB",
        "database": "MongoDB (store_demo)",
        "collection": "products",
        "endpoints": {
            "GET /products": "Lấy tất cả products",
            "GET /products/<id>": "Lấy 1 product theo ID",
            "POST /products": "Tạo product mới",
            "PUT /products/<id>": "Cập nhật product",
            "DELETE /products/<id>": "Xóa product"
        }
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')