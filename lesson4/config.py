import os

class Config:
    # Cập nhật URI với thông tin mới
    SQLALCHEMY_DATABASE_URI = f"postgresql://movieuser:moviepass123@localhost:5433/movie_booking_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = "movie-booking-secret-key"