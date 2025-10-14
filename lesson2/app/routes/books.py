from flask import Blueprint, jsonify, request, make_response
from app.models import Book
from app.extension import db, cache
from app.routes.auth import token_required, admin_required
from datetime import datetime
import hashlib
import base64

books_bp = Blueprint("books", __name__)

def generate_etag(data):
    """Tạo ETag từ dữ liệu"""
    return hashlib.md5(str(data).encode()).hexdigest()

def encode_cursor(book_id):
    """Encode book_id thành cursor string"""
    return base64.b64encode(str(book_id).encode()).decode()

def decode_cursor(cursor):
    """Decode cursor string thành book_id"""
    try:
        return int(base64.b64decode(cursor.encode()).decode())
    except:
        return None

@books_bp.route("/", methods=["GET"])
def get_books():
    # Xác định pagination strategy
    pagination_type = request.args.get('type', 'page')  # page, cursor, offset
    
    # Strategy 1: PAGE-BASED (offset/limit với page number)
    if pagination_type == 'page':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validation
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Query với pagination
        pagination = Book.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        books_data = [{
            "id": b.id, 
            "title": b.title, 
            "author": b.author, 
            "is_available": b.is_available
        } for b in pagination.items]
        
        response_data = {
            "data": books_data,
            "pagination": {
                "type": "page-based",
                "current_page": page,
                "per_page": per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
                "next_page": page + 1 if pagination.has_next else None,
                "prev_page": page - 1 if pagination.has_prev else None
            },
            "links": {
                "self": f"/books?type=page&page={page}&per_page={per_page}",
                "next": f"/books?type=page&page={page+1}&per_page={per_page}" if pagination.has_next else None,
                "prev": f"/books?type=page&page={page-1}&per_page={per_page}" if pagination.has_prev else None,
                "first": f"/books?type=page&page=1&per_page={per_page}",
                "last": f"/books?type=page&page={pagination.pages}&per_page={per_page}"
            }
        }
    
    # Strategy 2: CURSOR-BASED
    elif pagination_type == 'cursor':
        limit = request.args.get('limit', 10, type=int)
        cursor = request.args.get('cursor', None)
        
        if limit < 1 or limit > 100:
            limit = 10
        
        # Build query
        query = Book.query.order_by(Book.id)
        
        if cursor:
            cursor_id = decode_cursor(cursor)
            if cursor_id:
                query = query.filter(Book.id > cursor_id)
        
        # Lấy limit + 1 để biết có next page không
        books = query.limit(limit + 1).all()
        
        has_next = len(books) > limit
        if has_next:
            books = books[:limit]
        
        books_data = [{
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "is_available": b.is_available
        } for b in books]
        
        next_cursor = encode_cursor(books[-1].id) if books and has_next else None
        
        response_data = {
            "data": books_data,
            "pagination": {
                "type": "cursor-based",
                "limit": limit,
                "has_next": has_next,
                "next_cursor": next_cursor
            },
            "links": {
                "self": f"/books?type=cursor&limit={limit}" + (f"&cursor={cursor}" if cursor else ""),
                "next": f"/books?type=cursor&limit={limit}&cursor={next_cursor}" if next_cursor else None
            }
        }
    
    # Strategy 3: OFFSET-BASED (raw offset/limit)
    else:  # offset
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        if offset < 0:
            offset = 0
        if limit < 1 or limit > 100:
            limit = 10
        
        # Query
        total = Book.query.count()
        books = Book.query.offset(offset).limit(limit).all()
        
        books_data = [{
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "is_available": b.is_available
        } for b in books]
        
        has_next = (offset + limit) < total
        
        response_data = {
            "data": books_data,
            "pagination": {
                "type": "offset-based",
                "offset": offset,
                "limit": limit,
                "total_items": total,
                "has_next": has_next,
                "next_offset": offset + limit if has_next else None
            },
            "links": {
                "self": f"/books?type=offset&offset={offset}&limit={limit}",
                "next": f"/books?type=offset&offset={offset+limit}&limit={limit}" if has_next else None,
                "prev": f"/books?type=offset&offset={max(0, offset-limit)}&limit={limit}" if offset > 0 else None
            }
        }
    
    response = make_response(jsonify(response_data))
    response.headers['Cache-Control'] = 'public, max-age=60'
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
@books_bp.route("/author", methods=["GET"]) 
def search_books(): 
    """ DEMO: Cache key bao gồm query parameters /books/author?name=X và /books/author?name=Y là 2 cache entries khác nhau 
    GET /books/author?name=Martin&page=1&per_page=5 Cache key bao gồm query parameters """ 
    author = request.args.get('name', '').strip() 
    page = request.args.get('page', 1, type=int) 
    per_page = request.args.get('per_page', 10, type=int) 
    if page < 1: 
        page = 1 
    if per_page < 1 or per_page > 100: 
        per_page = 10 
    # Tạo cache key duy nhất dựa trên các tham số 
    cache_key = f"search_books_{author}_page{page}_per{per_page}" 
    cached_result = cache.get(cache_key) 
    if cached_result: 
        response = make_response(jsonify({ 
            "data": cached_result["books"], 
            "search": {"author": author if author else None}, 
            "pagination": cached_result["pagination"], 
            "from_cache": True 
        })) 
    else: 
        # Truy vấn DB 
        query = Book.query 
        if author: 
            query = query.filter(Book.author.ilike(f'%{author}%')) 
        pagination = query.paginate(page=page, per_page=per_page, error_out=False) 
        books_data = [{ 
            "id": b.id, 
            "title": b.title, 
            "author": b.author, 
            "is_available": b.is_available 
        } for b in pagination.items] 
        pagination_data = { 
            "current_page": page, 
            "per_page": per_page, 
            "total_pages": pagination.pages, 
            "total_items": pagination.total, 
            "has_next": pagination.has_next, 
            "has_prev": pagination.has_prev 
        } 
        # Lưu vào cache 
        cache.set(cache_key, { 
            "books": books_data, 
            "pagination": pagination_data 
        }, timeout=60) 
        response = make_response(jsonify({ 
            "data": books_data, 
            "search": {"author": author if author else None}, 
            "pagination": pagination_data, 
            "from_cache": False 
        })) 
    response.headers['Cache-Control'] = 'public, max-age=60' 
    response.headers['Vary'] = 'Accept-Language' 
    return response