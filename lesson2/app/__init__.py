from flask import Flask
from app.routes.books import books_bp
from app.routes.loans import loans_bp
from app.routes.users import users_bp
from app.routes.auth import auth_bp
from app.extension import db, cache

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    db.init_app(app)
    cache.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(loans_bp, url_prefix='/loans')
    app.register_blueprint(users_bp, url_prefix='/users')
    
    with app.app_context():
        db.create_all()
        
    return app