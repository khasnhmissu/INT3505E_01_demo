from flask import Blueprint, jsonify, request
from app.models import User, Loan
from app.extension import db
from app.routes.auth import token_required, admin_required
from sqlalchemy.orm import joinedload
import jwt  # MỚI: Để decode token trong demo
from config import Config

users_bp = Blueprint("users", __name__)

# ADMIN - Xem tất cả users (chỉ admin)
@users_bp.route("/", methods=["GET"])
@admin_required
def get_users(current_user):
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users])

# USER - Xem thông tin user (user xem được tất cả)
@users_bp.route("/<int:user_id>", methods=["GET"])
@token_required
def get_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role})

@users_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    })

@users_bp.route("/me", methods=["PUT"])
@token_required
def update_current_user(current_user):
    data = request.json
    
    if "name" in data and data["name"]:
        current_user.name = data["name"]
    
    if "email" in data and data["email"]:
        # Kiểm tra email mới có trùng với user khác không
        existing = User.query.filter(User.email == data["email"], User.id != current_user.id).first()
        if existing:
            return jsonify({"error": "Email đã tồn tại"}), 400
        current_user.email = data["email"]
    
    db.session.commit()
    return jsonify({"message": "User updated"})

@users_bp.route("/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(current_user, user_id):
    data = request.json
    user = User.query.get_or_404(user_id)
    
    if "name" in data and data["name"]:
        user.name = data["name"]
    
    if "email" in data and data["email"]:
        existing = User.query.filter(User.email == data["email"], User.id != user_id).first()
        if existing:
            return jsonify({"error": "Email đã tồn tại"}), 400
        user.email = data["email"]
    
    if "role" in data and data["role"] in ["user", "admin"]:
        user.role = data["role"]
    
    db.session.commit()
    return jsonify({"message": "User updated"})

@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})

@users_bp.route("/all-loans-v1", methods=["GET"])
@admin_required
def get_all_loans_v1(current_user):
    users = User.query.all()
    output = []
    for user in users:
        user_loans = []
        for loan in user.loans:
            user_loans.append({
                "loan_id": loan.loan_id,
                "book_title": loan.book.title,
                "checkout_date": str(loan.checkout_date),
                "return_date": str(loan.return_date) if loan.return_date else None
            })
        output.append({
            "user_id": user.id,
            "user_name": user.name,
            "loans": user_loans
        })
    return jsonify(output)

@users_bp.route("/all-loans-v2", methods=["GET"])
@admin_required
def get_all_loans_v2(current_user):
    users = User.query.options(
        joinedload(User.loans).joinedload(Loan.book)
    ).all()
    output = []
    for user in users:
        user_loans = []
        for loan in user.loans:
            user_loans.append({
                "loan_id": loan.loan_id,
                "book_title": loan.book.title,
                "checkout_date": str(loan.checkout_date),
                "return_date": str(loan.return_date) if loan.return_date else None
            })
        output.append({
            "user_id": user.id,
            "user_name": user.name,
            "loans": user_loans
        })
    return jsonify(output)

@users_bp.route("/<int:user_id>/loans", methods=["GET"])
@token_required
def get_user_loans(current_user, user_id):
    user = User.query.options(
        joinedload(User.loans).joinedload(Loan.book)
    ).get_or_404(user_id)
    
    user_loans = []
    for loan in user.loans:
        user_loans.append({
            "loan_id": loan.loan_id,
            "book_title": loan.book.title,
            "checkout_date": str(loan.checkout_date),
            "return_date": str(loan.return_date) if loan.return_date else None
        })
    
    return jsonify({
        "user_id": user.id,
        "user_name": user.name,
        "loans": user_loans
    })