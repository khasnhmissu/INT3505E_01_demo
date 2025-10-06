from flask import Blueprint, jsonify, request, make_response
from app.models import Loan, Book, User
from app.extension import db, cache
from datetime import date, datetime
from app.routes.auth import token_required, admin_required

loans_bp = Blueprint("loans", __name__)

# DEMO: no-cache - phải revalidate mỗi lần dùng
@loans_bp.route("/", methods=["GET"])
@admin_required
def get_loans(current_user):
    """
    DEMO: Cache-Control: no-cache
    - Được cache nhưng phải revalidate với server mỗi lần
    - Đảm bảo dữ liệu luôn mới nhất
    """
    loans = Loan.query.all()
    result = []
    for loan in loans:
        result.append({
            "loan_id": loan.loan_id,
            "book_id": loan.book_id,
            "book_title": loan.book.title,
            "user_id": loan.user_id,
            "user_name": loan.user.name,
            "checkout_date": str(loan.checkout_date),
            "return_date": str(loan.return_date) if loan.return_date else None
        })
    
    response = make_response(jsonify(result))
    
    # DEMO: no-cache - cache nhưng phải revalidate
    response.headers['Cache-Control'] = 'private, no-cache'
    response.headers['Vary'] = 'Authorization'
    
    return response

@loans_bp.route("/<int:loan_id>", methods=["GET"])
@token_required
def get_loan(current_user, loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    response = make_response(jsonify({
        "loan_id": loan.loan_id,
        "book_id": loan.book_id,
        "book_title": loan.book.title,
        "user_id": loan.user_id,
        "user_name": loan.user.name,
        "checkout_date": str(loan.checkout_date),
        "return_date": str(loan.return_date) if loan.return_date else None
    }))
    
    # Private cache với thời gian ngắn
    response.headers['Cache-Control'] = 'private, max-age=30'
    
    return response

@loans_bp.route("/checkout", methods=["POST"])
@token_required
def checkout_book(current_user):
    data = request.json
    
    if "book_id" not in data:
        return jsonify({"error": "Cần có book_id"}), 400
    
    book_id = data["book_id"]
    
    book = Book.query.get_or_404(book_id)
    
    if not book.is_available:
        return jsonify({"error": "Sách này đang được mượn"}), 400
    
    loan = Loan(
        book_id=book_id,
        user_id=current_user.id,
        checkout_date=date.today()
    )
    
    book.is_available = False
    
    db.session.add(loan)
    db.session.commit()
    
    # Xóa cache liên quan
    cache.delete_memoized(get_active_loans)
    
    response = make_response(jsonify({
        "message": "Mượn sách thành công",
        "loan_id": loan.loan_id,
        "checkout_date": str(loan.checkout_date)
    }), 201)
    
    response.headers['Cache-Control'] = 'no-store'
    
    return response

@loans_bp.route("/return/<int:loan_id>", methods=["PUT"])
@admin_required
def return_book(current_user, loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.return_date:
        return jsonify({"error": "Sách này đã được trả rồi"}), 400
    
    loan.return_date = date.today()
    
    book = Book.query.get(loan.book_id)
    book.is_available = True
    
    db.session.commit()
    
    # Xóa cache
    cache.delete_memoized(get_active_loans)
    
    response = make_response(jsonify({
        "message": "Trả sách thành công",
        "return_date": str(loan.return_date)
    }))
    
    response.headers['Cache-Control'] = 'no-store'
    
    return response

# DEMO: Cache với stale-while-revalidate
@loans_bp.route("/active", methods=["GET"])
@admin_required
@cache.cached(timeout=45)
def get_active_loans(current_user):
    """
    DEMO: stale-while-revalidate
    - Trả bản cũ trong khi revalidate ngầm
    - UX tốt hơn vì không phải chờ
    """
    active_loans = Loan.query.filter(Loan.return_date == None).all()
    result = []
    for loan in active_loans:
        result.append({
            "loan_id": loan.loan_id,
            "book_title": loan.book.title,
            "user_name": loan.user.name,
            "checkout_date": str(loan.checkout_date)
        })
    
    response = make_response(jsonify(result))
    
    # DEMO: stale-while-revalidate=30
    # Sau 45s hết hạn, trong 30s tiếp có thể trả stale và revalidate ngầm
    response.headers['Cache-Control'] = 'private, max-age=45, stale-while-revalidate=30'
    
    return response

# DEMO: Cache private cho dữ liệu user cá nhân
@loans_bp.route("/my-loans", methods=["GET"])
@token_required
def get_my_loans(current_user):
    """
    DEMO: Cache-Control: private
    - Chỉ cache ở browser của user
    - Không cache ở CDN/proxy vì dữ liệu riêng tư
    """
    # Tạo cache key riêng cho từng user
    cache_key = f"user_loans_{current_user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        response = make_response(jsonify(cached_data))
        response.headers['X-Cache-Status'] = 'HIT'
    else:
        loans = Loan.query.filter_by(user_id=current_user.id).all()
        result = []
        for loan in loans:
            result.append({
                "loan_id": loan.loan_id,
                "book_title": loan.book.title,
                "checkout_date": str(loan.checkout_date),
                "return_date": str(loan.return_date) if loan.return_date else "Chưa trả"
            })
        
        data = {
            "user_name": current_user.name,
            "loans": result
        }
        
        cache.set(cache_key, data, timeout=60)
        
        response = make_response(jsonify(data))
        response.headers['X-Cache-Status'] = 'MISS'
    
    # DEMO: private - chỉ browser cache, không CDN
    response.headers['Cache-Control'] = 'private, max-age=60'
    response.headers['Vary'] = 'Authorization'
    
    return response

@loans_bp.route("/user/<int:user_id>", methods=["GET"])
@admin_required
def get_user_loans(current_user, user_id):
    user = User.query.get_or_404(user_id)
    loans = Loan.query.filter_by(user_id=user_id).all()
    result = []
    for loan in loans:
        result.append({
            "loan_id": loan.loan_id,
            "book_title": loan.book.title,
            "checkout_date": str(loan.checkout_date),
            "return_date": str(loan.return_date) if loan.return_date else "Chưa trả"
        })
    
    response = make_response(jsonify({
        "user_name": user.name,
        "loans": result
    }))
    
    response.headers['Cache-Control'] = 'private, max-age=30'
    
    return response

@loans_bp.route("/<int:loan_id>", methods=["DELETE"])
@admin_required
def delete_loan(current_user, loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    if not loan.return_date:
        book = Book.query.get(loan.book_id)
        book.is_available = True
    
    db.session.delete(loan)
    db.session.commit()
    
    cache.delete_memoized(get_active_loans)
    
    response = make_response(jsonify({"message": "Đã xóa giao dịch"}))
    response.headers['Cache-Control'] = 'no-store'
    
    return response