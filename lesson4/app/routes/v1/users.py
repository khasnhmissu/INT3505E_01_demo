from flask import request, jsonify
from app.routes.v1 import v1_bp
from app.extension import db
from app.models import User, Booking

@v1_bp.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@v1_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@v1_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@v1_bp.route('/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    db.session.commit()
    return jsonify(user.to_dict()), 200

@v1_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@v1_bp.route('/users/<int:user_id>/bookings', methods=['GET'])
def list_user_bookings(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).all()
    return jsonify([booking.to_dict() for booking in bookings]), 200

@v1_bp.route('/users/<int:user_id>:send-verification-email', methods=['POST'])
def send_verification_email(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'message': f'Verification email sent to {user.email}'}), 200