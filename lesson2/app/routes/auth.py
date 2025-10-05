from flask import Blueprint, jsonify, request
from app.models import User
from app.extension import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from config import Config

auth_bp = Blueprint("auth", __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Cần đăng nhập"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({"error": "User không tồn tại"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Cần đăng nhập"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({"error": "User không tồn tại"}), 401
            
            # Kiểm tra quyền admin
            if current_user.role != "admin":
                return jsonify({"error": "Bạn không có quyền thực hiện hành động này"}), 403
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email và password là bắt buộc"}), 400
    
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email đã tồn tại"}), 400
    
    hashed_password = generate_password_hash(data["password"])
    
    user = User(
        name=data.get("name", "User"),
        email=data["email"],
        password=hashed_password
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "Đăng ký thành công",
        "user_id": user.id
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email và password là bắt buộc"}), 400
    
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Email hoặc password không đúng"}), 401
    
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm="HS256")

    return jsonify({
        "message": "Đăng nhập thành công",
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    })
    

@auth_bp.route("/create-admin", methods=["POST"])
def create_admin():
    data = request.json
    
    # Kiểm tra đã có admin chưa
    existing_admin = User.query.filter_by(role="admin").first()
    if existing_admin:
        return jsonify({"error": "Đã có admin trong hệ thống"}), 400
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email và password là bắt buộc"}), 400
    
    hashed_password = generate_password_hash(data["password"])
    
    admin = User(
        name=data.get("name", "Admin"),
        email=data["email"],
        password=hashed_password,
        role="admin"
    )
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({
        "message": "Tạo admin thành công",
        "user_id": admin.id
    }), 201