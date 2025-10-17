from flask import request, jsonify
from app.routes.v1 import v1_bp
from app.extension import db
from app.models import Booking

@v1_bp.route('/bookings', methods=['GET'])
def list_bookings():
    bookings = Booking.query.all()
    return jsonify([booking.to_dict() for booking in bookings]), 200

@v1_bp.route('/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return jsonify(booking.to_dict()), 200

@v1_bp.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    booking = Booking(
        user_id=data['user_id'],
        movie_id=data['movie_id'],
        theater_id=data.get('theater_id'),
        seat_number=data.get('seat_number')
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify(booking.to_dict()), 201

@v1_bp.route('/bookings/<int:booking_id>', methods=['PATCH'])
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()
    if 'seat_number' in data:
        booking.seat_number = data['seat_number']
    if 'theater_id' in data:
        booking.theater_id = data['theater_id']
    db.session.commit()
    return jsonify(booking.to_dict()), 200

@v1_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    return '', 204