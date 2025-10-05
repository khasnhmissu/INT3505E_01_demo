import os

class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://myuser:mypassword@localhost:5432/mydatabase"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = "my-secret-key"