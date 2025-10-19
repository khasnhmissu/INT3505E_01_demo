from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from app.extension import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    from app.routes.v1 import v1_bp
    from app.routes.v2 import v2_bp
    app.register_blueprint(v1_bp, url_prefix='/v1')
    app.register_blueprint(v2_bp, url_prefix='/v2')
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    with app.app_context():
        db.create_all()
    
    return app