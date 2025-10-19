from flask import request, jsonify
from app.routes.v2 import v2_bp
from app.extension import db
from app.models import Movie

# V2 CHANGE: Helper function để tạo response envelope với pagination
def create_paginated_response(query, page, per_page):
    """
    Tạo response có cấu trúc envelope với thông tin phân trang
    """
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'data': [movie.to_dict() for movie in paginated.items],
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total_pages': paginated.pages,
            'total_items': paginated.total,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    }


@v2_bp.route('/movies', methods=['GET'])
def list_movies():
    """
    V2 CHANGE: Thêm pagination bắt buộc
    - Query params: page (default=1), per_page (default=10)
    - Response có envelope structure với data và pagination info
    """
    search = request.args.get('search')
    genre = request.args.get('genre')
    
    # Lấy pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Giới hạn per_page để tránh abuse
    per_page = min(per_page, 100)
    
    # Build query với filters
    query = Movie.query
    if search:
        query = query.filter(Movie.title.ilike(f'%{search}%'))
    if genre:
        query = query.filter_by(genre=genre)
    
    # V2 CHANGE: Sử dụng pagination thay vì query.all()
    response = create_paginated_response(query, page, per_page)
    
    return jsonify(response), 200


@v2_bp.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    """
    Lấy thông tin chi tiết một movie
    Logic tương tự v1
    """
    movie = Movie.query.get_or_404(movie_id)
    return jsonify(movie.to_dict()), 200


@v2_bp.route('/movies', methods=['POST'])
def create_movie():
    """
    Tạo movie mới
    Logic tương tự v1
    """
    data = request.get_json()
    
    # Có thể thêm validation ở đây
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    movie = Movie(
        title=data['title'],
        genre=data.get('genre'),
        duration=data.get('duration')
    )
    db.session.add(movie)
    db.session.commit()
    
    return jsonify(movie.to_dict()), 201


@v2_bp.route('/movies/<int:movie_id>', methods=['PATCH'])
def update_movie(movie_id):
    """
    Cập nhật thông tin movie
    Logic tương tự v1
    """
    movie = Movie.query.get_or_404(movie_id)
    data = request.get_json()
    
    if 'title' in data:
        movie.title = data['title']
    if 'genre' in data:
        movie.genre = data['genre']
    if 'duration' in data:
        movie.duration = data['duration']
    
    db.session.commit()
    return jsonify(movie.to_dict()), 200


@v2_bp.route('/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """
    Xóa movie
    Logic tương tự v1
    """
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    
    return '', 204


# V2 CHANGE: Refactor custom action từ /movies:import sang /movies/import
# Đây là chuẩn REST hơn, sử dụng "/" thay vì ":"
@v2_bp.route('/movies/import', methods=['POST'])
def import_movies():
    """
    V2 CHANGE: Route đã được refactor từ /movies:import thành /movies/import
    Import nhiều movies cùng lúc
    """
    data = request.get_json()
    
    if not data or 'movies' not in data:
        return jsonify({'error': 'Movies data is required'}), 400
    
    movies_data = data.get('movies', [])
    imported_count = 0
    errors = []
    
    for idx, movie_data in enumerate(movies_data):
        # Validation
        if 'title' not in movie_data:
            errors.append(f'Movie at index {idx} missing title')
            continue
        
        try:
            movie = Movie(
                title=movie_data['title'],
                genre=movie_data.get('genre'),
                duration=movie_data.get('duration')
            )
            db.session.add(movie)
            imported_count += 1
        except Exception as e:
            errors.append(f'Movie at index {idx}: {str(e)}')
    
    db.session.commit()
    
    response = {
        'message': f'{imported_count} movies imported successfully',
        'imported_count': imported_count
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), 201


# Vì bookings vẫn thuộc v1, client phải gọi /api/v1/bookings
# hoặc /api/v1/movies/<id>/bookings nếu cần