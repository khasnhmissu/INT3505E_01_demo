from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./order_management.db"
    API_TITLE: str = "Order Management API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()