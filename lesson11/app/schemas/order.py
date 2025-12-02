from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus

class OrderBase(BaseModel):
    customer_name: str
    product_id: int
    quantity: int

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    quantity: Optional[int] = None

class OrderResponse(OrderBase):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    # HATEOAS: Links để client biết các actions tiếp theo
    links: Optional[dict] = None
    
    class Config:
        from_attributes = True

class WebhookSubscriptionCreate(BaseModel):
    url: str
    event_type: str

class WebhookSubscriptionResponse(BaseModel):
    id: int
    url: str
    event_type: str
    is_active: bool
    
    class Config:
        from_attributes = True