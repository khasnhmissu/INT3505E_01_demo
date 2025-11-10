from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from app.routes.books import books_bp
from app.routes.loans import loans_bp
from app.routes.users import users_bp
from app.routes.auth import auth_bp
from app.extension import db, cache
import os

def create_app(config_name=None):
    app = Flask(__name__)

    # Swagger UI setup
    SWAGGER_URL = '/apidocs'
    API_URL = '/swagger.yaml'  # Swagger UI sẽ gọi endpoint này

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Library Management System API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/swagger.yaml')
    def swagger_yaml():
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        yaml_path = os.path.join(project_root, 'static', 'docs')

        return send_from_directory(
            yaml_path,
            'swagger.yaml',
            mimetype='application/yaml'
        )
        
    @app.route("/cache")
    def debug_cache():
        print("CACHE hiện tại:", cache.cache._cache)
        return {"cache": list(cache.cache._cache.keys())}

    # CORS và Config
    CORS(app)
    
    if config_name:
        from config import config_by_name
        app.config.from_object(config_by_name[config_name])
    else:
        # Default: load từ config.Config
        app.config.from_object('config.Config')
         
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Init extension
    db.init_app(app)
    cache.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(loans_bp, url_prefix='/loans')
    app.register_blueprint(users_bp, url_prefix='/users')
    
    with app.app_context():
        if not app.config.get('TESTING', False):
            db.create_all()
        
    return app
