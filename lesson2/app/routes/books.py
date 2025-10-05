from flask import Blueprint, jsonify, request
from app.models import Book
from app.extension import db
from app.routes.auth import token_required, admin_required

books_bp = Blueprint("books", __name__)

@books_bp.route("/", methods=["GET"])
def get_books():
    books = Book.query.all()
    return jsonify([{"id": b.id, "title": b.title, "author": b.author, "is_available": b.is_available} for b in books])

@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify({"id": book.id, "title": book.title, 
                    "author": book.author,
                    "is_available": book.is_available})

@books_bp.route("/", methods=["POST"])
@admin_required
def add_book(current_user):
    data = request.json
    book = Book(title=data["title"], 
                author=data.get("author"),
                is_available=data.get("is_available", True))
    db.session.add(book)
    db.session.commit()
    return jsonify({"message": "Book added", "id": book.id}), 201

@books_bp.route("/<int:book_id>", methods=["PUT"])
@admin_required
def update_book(current_user, book_id):
    data = request.json
    book = Book.query.get_or_404(book_id)
   
    if "title" in data and data["title"]:  
        book.title = data["title"]
    
    if "author" in data:
        book.author = data["author"]
        
    if "is_available" in data and data["is_available"] is not None:  
        book.is_available = bool(data["is_available"])
   
    db.session.commit()
    return jsonify({"message": "Book updated"})

@books_bp.route("/<int:book_id>", methods=["DELETE"])
@admin_required
def delete_book(current_user, book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"})