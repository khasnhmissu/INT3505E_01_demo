from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics

db = SQLAlchemy()
cache = Cache()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://"
)
# ✅ Khởi tạo metrics NGOÀI hàm
metrics = PrometheusMetrics.for_app_factory()

def init_extensions(app):
    """Initialize Flask extensions"""
    global metrics  # ✅ Sử dụng global
    
    db.init_app(app)
    cache.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # ✅ Initialize Prometheus Metrics
    metrics.init_app(app)
    
    # Add custom info
    metrics.info('app_info', 'Library Management System API', version='1.0.0')
    
    app.logger.info("✅ All extensions initialized (including Prometheus /metrics)")
    
    return app