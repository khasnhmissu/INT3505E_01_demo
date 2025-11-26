import os

class Config:
    # ✅ ĐỌC TỪ ENVIRONMENT VARIABLE
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://myuser:mypassword@localhost:5432/mydatabase'  # fallback cho local dev
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'my-secret-key')
    
    # Observability Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # Rate Limiting Configuration
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "100 per minute"
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAIL_MAX = int(os.getenv('CIRCUIT_BREAKER_FAIL_MAX', '5'))
    CIRCUIT_BREAKER_TIMEOUT = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60'))
    
class TestConfig(Config):
    """Config cho Testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class DevelopmentConfig(Config):
    """Config cho Development"""
    DEBUG = True
    
config_by_name = {
    'testing': TestConfig,
    'development': DevelopmentConfig,
}

