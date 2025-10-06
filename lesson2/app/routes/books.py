from flask import Blueprint, jsonify, request, make_response
from app.models import Book
from app.extension import db, cache
from app.routes.auth import token_required, admin_required
from datetime import datetime
import hashlib

books_bp = Blueprint("books", __name__)

def generate_etag(data):
    """Tạo ETag từ dữ liệu"""
    return hashlib.md5(str(data).encode()).hexdigest()

# DEMO: Cache-Control với max-age và public
@books_bp.route("/", methods=["GET"])
@cache.cached(timeout=60, query_string=True)  # Cache 60s
def get_books():
    """
    DEMO: Server-side cache (60s) + Cache-Control headers
    - Lần đầu: query DB, lưu cache
    - Lần sau (trong 60s): trả từ cache
    """
    books = Book.query.all()
    books_data = [{"id": b.id, "title": b.title, "author": b.author, "is_available": b.is_available} for b in books]
    
    response = make_response(jsonify(books_data))
    
    # DEMO Cache-Control: public, max-age
    response.headers['Cache-Control'] = 'public, max-age=60'
    
    # DEMO Vary header - cache key phụ thuộc Accept-Language
    response.headers['Vary'] = 'Accept-Language'
    
    return response

# DEMO: ETag + Last-Modified + Conditional Requests
@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    """
    DEMO: ETag & Last-Modified validators
    - Client gửi If-None-Match (ETag) hoặc If-Modified-Since
    - Server trả 304 Not Modified nếu chưa đổi
    """
    book = Book.query.get_or_404(book_id)
    book_data = {
        "id": book.id, 
        "title": book.title, 
        "author": book.author,
        "is_available": book.is_available
    }
    
    # Tạo ETag từ dữ liệu sách
    etag = generate_etag(book_data)
    
    # Giả sử last_modified (thực tế nên có timestamp trong DB)
    last_modified = datetime.utcnow().replace(microsecond=0)
    
    # Kiểm tra If-None-Match (ETag validation)
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match == etag:
        # DEMO: 304 Not Modified - không gửi body
        response = make_response('', 304)
        response.headers['ETag'] = etag
        response.headers['Cache-Control'] = 'private, max-age=30, must-revalidate'
        return response
    
    # Kiểm tra If-Modified-Since (Last-Modified validation)
    if_modified_since = request.headers.get('If-Modified-Since')
    if if_modified_since:
        try:
            ims_date = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
            if last_modified <= ims_date:
                response = make_response('', 304)
                response.headers['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
                response.headers['Cache-Control'] = 'private, max-age=30, must-revalidate'
                return response
        except ValueError:
            pass
    
    # Trả dữ liệu mới với validators
    response = make_response(jsonify(book_data))
    response.headers['ETag'] = etag
    response.headers['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # DEMO Cache-Control: private (chỉ browser cache), must-revalidate
    response.headers['Cache-Control'] = 'private, max-age=30, must-revalidate'
    
    return response

# DEMO: Cache-Control no-store cho dữ liệu nhạy cảm
@books_bp.route("/", methods=["POST"])
@admin_required
def add_book(current_user):
    """
    DEMO: no-store - không cache ở đâu cả
    """
    data = request.json
    book = Book(title=data["title"], 
                author=data.get("author"),
                is_available=data.get("is_available", True))
    db.session.add(book)
    db.session.commit()
    
    # Xóa cache danh sách sách khi thêm mới
    cache.delete_memoized(get_books)
    
    response = make_response(jsonify({"message": "Book added", "id": book.id}), 201)
    
    # DEMO: no-store - không được cache
    response.headers['Cache-Control'] = 'no-store'
    
    return response

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
    
    # Xóa cache khi cập nhật
    cache.delete_memoized(get_books)
    
    response = make_response(jsonify({"message": "Book updated"}))
    response.headers['Cache-Control'] = 'no-store'
    
    return response

@books_bp.route("/<int:book_id>", methods=["DELETE"])
@admin_required
def delete_book(current_user, book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    
    # Xóa cache khi xóa sách
    cache.delete_memoized(get_books)
    
    response = make_response(jsonify({"message": "Book deleted"}))
    response.headers['Cache-Control'] = 'no-store'
    
    return response

# DEMO: Cache với query parameters khác nhau
@books_bp.route("/search", methods=["GET"])
def search_books():
    """
    DEMO: Cache key bao gồm query parameters
    /books/search?author=X và /books/search?author=Y là 2 cache entries khác nhau
    """
    author = request.args.get('author', '').strip()
    
    # Tạo cache key từ query params
    cache_key = f"search_books_{author}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        # Cache hit
        response = make_response(jsonify({
            "books": cached_result,
            "from_cache": True
        }))
    else:
        # Cache miss
        if author:
            books = Book.query.filter(Book.author.ilike(f'%{author}%')).all()
        else:
            books = Book.query.all()
        
        books_data = [{"id": b.id, "title": b.title, "author": b.author, "is_available": b.is_available} for b in books]
        
        # Lưu vào cache
        cache.set(cache_key, books_data, timeout=60)
        
        response = make_response(jsonify({
            "books": books_data,
            "from_cache": False
        }))
    
    # DEMO: Vary header cho search
    response.headers['Cache-Control'] = 'public, max-age=60'
    response.headers['Vary'] = 'Accept-Language'
    
    return response
