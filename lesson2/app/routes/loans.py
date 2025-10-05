from flask import Blueprint, jsonify, request
from app.models import Loan, Book, User
from app.extension import db
from datetime import date
from app.routes.auth import token_required, admin_required

loans_bp = Blueprint("loans", __name__)

@loans_bp.route("/", methods=["GET"])
@admin_required
def get_loans(current_user):
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
    return jsonify(result)

@loans_bp.route("/<int:loan_id>", methods=["GET"])
@token_required
def get_loan(current_user, loan_id):
    loan = Loan.query.get_or_404(loan_id)
    return jsonify({
        "loan_id": loan.loan_id,
        "book_id": loan.book_id,
        "book_title": loan.book.title,
        "user_id": loan.user_id,
        "user_name": loan.user.name,
        "checkout_date": str(loan.checkout_date),
        "return_date": str(loan.return_date) if loan.return_date else None
    })

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
    
    return jsonify({
        "message": "Mượn sách thành công",
        "loan_id": loan.loan_id,
        "checkout_date": str(loan.checkout_date)
    }), 201

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
    
    return jsonify({
        "message": "Trả sách thành công",
        "return_date": str(loan.return_date)
    })

@loans_bp.route("/active", methods=["GET"])
@admin_required
def get_active_loans(current_user):
    active_loans = Loan.query.filter(Loan.return_date == None).all()
    result = []
    for loan in active_loans:
        result.append({
            "loan_id": loan.loan_id,
            "book_title": loan.book.title,
            "user_name": loan.user.name,
            "checkout_date": str(loan.checkout_date)
        })
    return jsonify(result)

@loans_bp.route("/my-loans", methods=["GET"])
@token_required
def get_my_loans(current_user):
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    result = []
    for loan in loans:
        result.append({
            "loan_id": loan.loan_id,
            "book_title": loan.book.title,
            "checkout_date": str(loan.checkout_date),
            "return_date": str(loan.return_date) if loan.return_date else "Chưa trả"
        })
    return jsonify({
        "user_name": current_user.name,
        "loans": result
    })

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
    return jsonify({
        "user_name": user.name,
        "loans": result
    })

@loans_bp.route("/<int:loan_id>", methods=["DELETE"])
@admin_required
def delete_loan(current_user, loan_id):
    loan = Loan.query.get_or_404(loan_id)
    
    if not loan.return_date:
        book = Book.query.get(loan.book_id)
        book.is_available = True
    
    db.session.delete(loan)
    db.session.commit()
    return jsonify({"message": "Đã xóa giao dịch"})