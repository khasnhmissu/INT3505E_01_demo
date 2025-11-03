from flask import Blueprint, jsonify, request
from app.models import User
from app.extension import db, cache
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from config import Config
import uuid

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
            
            # MỚI: Kiểm tra xem token có trong blacklist không
            jti = data.get('jti')
            if jti:
                blacklisted = cache.get(f"blacklist:{jti}")
                if blacklisted:
                    return jsonify({"error": "Token đã bị vô hiệu hóa"}), 401
            
            current_user = User.query.get(data['user_id'])
            if data.get("token_version") != current_user.token_version:
                return jsonify({"error": "Token đã cũ, vui lòng đăng nhập lại"}), 401
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
            
            # MỚI: Kiểm tra blacklist
            jti = data.get('jti')
            if jti:
                blacklisted = cache.get(f"blacklist:{jti}")
                if blacklisted:
                    return jsonify({"error": "Token đã bị vô hiệu hóa"}), 401
            
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
    """
    - access_token: Thời hạn ngắn (15 phút), dùng để truy cập API
    - refresh_token: Thời hạn dài (7 ngày), dùng để lấy access_token mới
    """
    data = request.json
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email và password là bắt buộc"}), 400
    
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Email hoặc password không đúng"}), 401
    
    access_token_jti = str(uuid.uuid4())
    access_token = jwt.encode({
        'user_id': user.id,
        'jti': access_token_jti,
        'type': 'access',
        'token_version': user.token_version,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    refresh_token_jti = str(uuid.uuid4())
    refresh_token = jwt.encode({
        'user_id': user.id,
        'jti': refresh_token_jti,
        'type': 'refresh',
        'token_version': user.token_version,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, Config.SECRET_KEY, algorithm="HS256")

    return jsonify({
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 900,  # 15 minutes in seconds
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
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
    
@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    """    
    Headers:
        Authorization: Bearer <access_token>
    
    Request Body:
    {
        "refresh_token": "eyJhbGc..."
    }
    
    Cơ chế:
    1. Lấy access_token từ header
    2. Lấy refresh_token từ body
    3. Thêm jti của cả 2 tokens vào blacklist (cache)
    4. Blacklist tự động hết hạn khi token hết hạn
    """
    data = request.json
    
    # Lấy access token từ header
    access_token = request.headers.get('Authorization')
    if access_token and access_token.startswith('Bearer '):
        access_token = access_token[7:]
    
    try:
        # MỚI: Blacklist access_token
        access_payload = jwt.decode(access_token, Config.SECRET_KEY, algorithms=["HS256"])
        access_jti = access_payload.get('jti')
        if access_jti:
            # Thời gian timeout = thời gian còn lại của token
            exp_timestamp = access_payload.get('exp')
            remaining_time = exp_timestamp - datetime.datetime.utcnow().timestamp()
            if remaining_time > 0:
                cache.set(f"blacklist:{access_jti}", True, timeout=int(remaining_time))
        
        # MỚI: Blacklist refresh_token nếu có
        refresh_token = data.get("refresh_token")
        if refresh_token:
            refresh_payload = jwt.decode(refresh_token, Config.SECRET_KEY, algorithms=["HS256"])
            refresh_jti = refresh_payload.get('jti')
            if refresh_jti:
                exp_timestamp = refresh_payload.get('exp')
                remaining_time = exp_timestamp - datetime.datetime.utcnow().timestamp()
                if remaining_time > 0:
                    cache.set(f"blacklist:{refresh_jti}", True, timeout=int(remaining_time))
        
        return jsonify({"message": "Đăng xuất thành công"})
        
    except jwt.InvalidTokenError:
        # Nếu token không decode được, vẫn return success
        return jsonify({"message": "Đăng xuất thành công"})

# MỚI: Logout tất cả thiết bị bằng cách tăng token_version
@auth_bp.route("/logout-all", methods=["POST"])
@token_required
def logout_all_devices(current_user):
    """
    Cơ chế:
    - Tăng token_version của user lên 1
    - Tất cả refresh_tokens cũ (có token_version cũ) sẽ bị reject
    - Access tokens hiện tại vẫn hoạt động đến khi hết hạn (15 phút)
    """
    current_user.token_version += 1
    db.session.commit()
    
    return jsonify({
        "message": "Đã đăng xuất khỏi tất cả thiết bị",
        "new_token_version": current_user.token_version
    })
    
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Request Body:
    {
        "refresh_token": "eyJhbGc..."
    }
    
    Response:
    {
        "access_token": "eyJhbGc...",
        "expires_in": 900
    }
    """
    data = request.json
    
    if not data or not data.get("refresh_token"):
        return jsonify({"error": "Cần có refresh_token"}), 400
    
    refresh_token = data["refresh_token"]
    
    try:
        # Decode và validate refresh token
        payload = jwt.decode(refresh_token, Config.SECRET_KEY, algorithms=["HS256"])
        
        # Kiểm tra đây có phải refresh token không
        if payload.get('type') != 'refresh':
            return jsonify({"error": "Token không hợp lệ"}), 401
        
        # MỚI: Kiểm tra refresh token có trong blacklist không
        jti = payload.get('jti')
        if jti:
            blacklisted = cache.get(f"blacklist:{jti}")
            if blacklisted:
                return jsonify({"error": "Refresh token đã bị vô hiệu hóa"}), 401
        
        # Lấy user
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({"error": "User không tồn tại"}), 401
        
        # MỚI: Kiểm tra token_version - nếu không khớp, refresh token đã cũ
        token_version = payload.get('token_version', 0)
        if token_version != user.token_version:
            return jsonify({"error": "Refresh token đã hết hạn (version cũ)"}), 401
        
        # KHUYẾN NGHỊ: Trong production, nên blacklist refresh token sau khi dùng
        # và issue một refresh token mới (token rotation)
        # cache.set(f"blacklist:{jti}", True, timeout=7*24*60*60)
        
        # Tạo access_token mới
        new_access_token_jti = str(uuid.uuid4())
        new_access_token = jwt.encode({
            'user_id': user.id,
            'jti': new_access_token_jti,
            'type': 'access',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, Config.SECRET_KEY, algorithm="HS256")
        
        return jsonify({
            "access_token": new_access_token,
            "expires_in": 900
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token đã hết hạn, vui lòng đăng nhập lại"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Refresh token không hợp lệ"}), 401