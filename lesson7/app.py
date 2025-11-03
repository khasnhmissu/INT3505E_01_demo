# app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop Dell XPS 13", "price": 1200, "stock": 15},
    {"id": 2, "name": "Chuột Logitech MX Master", "price": 99, "stock": 50},
    {"id": 3, "name": "Bàn phím cơ Keychron K2", "price": 89, "stock": 30}
]

next_id = 4


def find_product_by_id(product_id):
    """Tìm product trong danh sách theo ID"""
    for product in products:
        if product['id'] == product_id:
            return product
    return None


@app.route('/products', methods=['GET'])
def get_all_products():
    """
    Lấy danh sách tất cả products
    Method: GET
    URL: http://localhost:5000/products
    """
    return jsonify({
        "success": True,
        "data": products,
        "total": len(products)
    }), 200


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Lấy thông tin 1 product theo ID
    Method: GET
    URL: http://localhost:5000/products/1
    """
    product = find_product_by_id(product_id)
    
    if product is None:
        return jsonify({
            "success": False,
            "message": f"Product với ID {product_id} không tồn tại"
        }), 404
    
    return jsonify({
        "success": True,
        "data": product
    }), 200


@app.route('/products', methods=['POST'])
def create_product():
    """
    Tạo product mới
    Method: POST
    URL: http://localhost:5000/products
    Body (JSON):
    {
        "name": "Tên sản phẩm",
        "price": 100,
        "stock": 20
    }
    """
    global next_id
    
    # Lấy dữ liệu JSON từ request
    data = request.get_json()
    
    # Kiểm tra dữ liệu đầu vào
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({
            "success": False,
            "message": "Thiếu thông tin 'name' hoặc 'price'"
        }), 400
    
    # Tạo product mới
    new_product = {
        "id": next_id,
        "name": data['name'],
        "price": data['price'],
        "stock": data.get('stock', 0)  # Mặc định stock = 0 nếu không có
    }
    
    # Thêm vào danh sách
    products.append(new_product)
    next_id += 1
    
    return jsonify({
        "success": True,
        "message": "Tạo product thành công",
        "data": new_product
    }), 201  # 201 = Created


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Cập nhật thông tin product
    Method: PUT
    URL: http://localhost:5000/products/1
    Body (JSON):
    {
        "name": "Tên mới",
        "price": 150,
        "stock": 25
    }
    """
    product = find_product_by_id(product_id)
    
    if product is None:
        return jsonify({
            "success": False,
            "message": f"Product với ID {product_id} không tồn tại"
        }), 404
    
    # Lấy dữ liệu cập nhật
    data = request.get_json()
    
    # Cập nhật các trường (giữ nguyên giá trị cũ nếu không có trong request)
    product['name'] = data.get('name', product['name'])
    product['price'] = data.get('price', product['price'])
    product['stock'] = data.get('stock', product['stock'])
    
    return jsonify({
        "success": True,
        "message": "Cập nhật product thành công",
        "data": product
    }), 200


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Xóa product
    Method: DELETE
    URL: http://localhost:5000/products/1
    """
    product = find_product_by_id(product_id)
    
    if product is None:
        return jsonify({
            "success": False,
            "message": f"Product với ID {product_id} không tồn tại"
        }), 404
    
    # Xóa khỏi danh sách
    products.remove(product)
    
    return jsonify({
        "success": True,
        "message": f"Đã xóa product ID {product_id}"
    }), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🚀 Product API - Flask CRUD Demo",
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