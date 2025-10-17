from flask import request, jsonify
from app.routes.v1 import v1_bp
from app.extension import db
from app.models import Theater

@v1_bp.route('/theaters', methods=['GET'])
def list_theaters():
    theaters = Theater.query.all()
    return jsonify([theater.to_dict() for theater in theaters]), 200

@v1_bp.route('/theaters/<int:theater_id>', methods=['GET'])
def get_theater(theater_id):
    theater = Theater.query.get_or_404(theater_id)
    return jsonify(theater.to_dict()), 200

@v1_bp.route('/theaters', methods=['POST'])
def create_theater():
    data = request.get_json()
    theater = Theater(
        name=data['name'],
        location=data.get('location'),
        capacity=data.get('capacity')
    )
    db.session.add(theater)
    db.session.commit()
    return jsonify(theater.to_dict()), 201

@v1_bp.route('/theaters/<int:theater_id>', methods=['PATCH'])
def update_theater(theater_id):
    theater = Theater.query.get_or_404(theater_id)
    data = request.get_json()
    if 'name' in data:
        theater.name = data['name']
    if 'location' in data:
        theater.location = data['location']
    if 'capacity' in data:
        theater.capacity = data['capacity']
    db.session.commit()
    return jsonify(theater.to_dict()), 200

@v1_bp.route('/theaters/<int:theater_id>', methods=['DELETE'])
def delete_theater(theater_id):
    theater = Theater.query.get_or_404(theater_id)
    db.session.delete(theater)
    db.session.commit()
    return '', 204