from flask import Blueprint

v1_bp = Blueprint('v1', __name__)

from app.routes.v1 import users, movies, theaters, bookings