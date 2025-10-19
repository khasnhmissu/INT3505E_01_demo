from flask import Blueprint

# Tạo Blueprint cho API v2
v2_bp = Blueprint('v2', __name__)

# Import các route sau khi blueprint được tạo để tránh circular import
from app.routes.v2 import movies