from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from datetime import datetime
import enum
from app.database import Base

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    product_id = Column(Integer, index=True)
    quantity = Column(Integer)
    total_amount = Column(Float)
    status = Column(String, default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    event_type = Column(String)  # order.created, order.completed, etc.
    is_active = Column(Integer, default=1)