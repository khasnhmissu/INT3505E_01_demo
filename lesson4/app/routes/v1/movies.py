from flask import request, jsonify
from app.routes.v1 import v1_bp
from app.extension import db
from app.models import Movie, Booking

@v1_bp.route('/movies', methods=['GET'])
def list_movies():
    search = request.args.get('search')
    genre = request.args.get('genre')
    
    query = Movie.query
    if search:
        query = query.filter(Movie.title.ilike(f'%{search}%'))
    if genre:
        query = query.filter_by(genre=genre)
    
    movies = query.all()
    return jsonify([movie.to_dict() for movie in movies]), 200

@v1_bp.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return jsonify(movie.to_dict()), 200

@v1_bp.route('/movies', methods=['POST'])
def create_movie():
    data = request.get_json()
    movie = Movie(
        title=data['title'],
        genre=data.get('genre'),
        duration=data.get('duration')
    )
    db.session.add(movie)
    db.session.commit()
    return jsonify(movie.to_dict()), 201

@v1_bp.route('/movies/<int:movie_id>', methods=['PATCH'])
def update_movie(movie_id):
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

@v1_bp.route('/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return '', 204

@v1_bp.route('/movies/<int:movie_id>/bookings', methods=['GET'])
def list_movie_bookings(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    bookings = Booking.query.filter_by(movie_id=movie_id).all()
    return jsonify([booking.to_dict() for booking in bookings]), 200

@v1_bp.route('/movies:import', methods=['POST'])
def import_movies():
    data = request.get_json()
    movies_data = data.get('movies', [])
    imported_count = 0
    for movie_data in movies_data:
        movie = Movie(
            title=movie_data['title'],
            genre=movie_data.get('genre'),
            duration=movie_data.get('duration')
        )
        db.session.add(movie)
        imported_count += 1
    db.session.commit()
    return jsonify({'message': f'{imported_count} movies imported successfully'}), 201