import os

class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://myuser:mypassword@localhost:5432/mydatabase"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = "my-secret-key"
    
class TestConfig(Config):
    """Config cho Testing"""
    TESTING = True
    # Dùng SQLite in-memory cho test - NHANH, SẠCH, KHÔNG CẦN DOCKER
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Hoặc dùng file SQLite nếu muốn debug
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    
    
class DevelopmentConfig(Config):
    """Config cho Development"""
    DEBUG = True
    
config_by_name = {
    'testing': TestConfig,
    'development': DevelopmentConfig,
}

