# app/__init__.py
from flask import Flask, jsonify
from flask_pymongo import PyMongo
import os

# Khởi tạo PyMongo (sẽ được bind với app sau)
mongo = PyMongo()

def create_app():
    """
    Application Factory Pattern
    Tạo và cấu hình Flask app với MongoDB và Blueprints
    """
    app = Flask(__name__)
    
    # ========================================
    # 1. CẤU HÌNH MONGODB
    # ========================================
    # Lấy MONGO_URI từ biến môi trường hoặc dùng mặc định
    app.config["MONGO_URI"] = os.getenv(
        "MONGO_URI", 
        "mongodb://localhost:27017/shop_manager"
    )
    
    # Khởi tạo PyMongo với app
    mongo.init_app(app)
    
    # ========================================
    # 2. ĐĂNG KÝ BLUEPRINTS
    # ========================================
    # Import blueprints
    from routes.products import products_bp
    from routes.customers import customers_bp
    from routes.orders import orders_bp
    
    # Đăng ký các blueprints với URL prefix
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(customers_bp, url_prefix='/api')
    app.register_blueprint(orders_bp, url_prefix='/api')
    
    # ========================================
    # 3. ROUTE TRANG CHỦ
    # ========================================
    @app.route('/', methods=['GET'])
    def home():
        """API Documentation"""
        return jsonify({
            "message": "🏪 Shop Management System API",
            "version": "1.0.0",
            "database": "MongoDB (shop_manager)",
            "resources": {
                "products": {
                    "GET /api/products": "Lấy tất cả products",
                    "GET /api/products/<id>": "Lấy 1 product",
                    "POST /api/products": "Tạo product mới",
                    "PUT /api/products/<id>": "Cập nhật product",
                    "DELETE /api/products/<id>": "Xóa product"
                },
                "customers": {
                    "GET /api/customers": "Lấy tất cả customers",
                    "GET /api/customers/<id>": "Lấy 1 customer",
                    "POST /api/customers": "Tạo customer mới",
                    "PUT /api/customers/<id>": "Cập nhật customer",
                    "DELETE /api/customers/<id>": "Xóa customer"
                },
                "orders": {
                    "GET /api/orders": "Lấy tất cả orders",
                    "GET /api/orders/<id>": "Lấy 1 order",
                    "POST /api/orders": "Tạo order mới",
                    "PUT /api/orders/<id>": "Cập nhật order",
                    "DELETE /api/orders/<id>": "Xóa order"
                }
            }
        }), 200
    
    # ========================================
    # 4. ERROR HANDLERS
    # ========================================
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Endpoint không tồn tại"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "message": "Lỗi server nội bộ"
        }), 500
    
    return app