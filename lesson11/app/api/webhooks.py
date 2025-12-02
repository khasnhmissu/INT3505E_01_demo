"""
Webhook Management API
- Subscribe/unsubscribe webhooks
- Webhook receiver endpoint để test
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.order import WebhookSubscription
from app.schemas.order import WebhookSubscriptionCreate, WebhookSubscriptionResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/subscribe", response_model=WebhookSubscriptionResponse, status_code=201)
def subscribe_webhook(subscription: WebhookSubscriptionCreate, db: Session = Depends(get_db)):
    """
    Subscribe to webhook events
    
    Available event types:
    - order.created
    - order.processing
    - order.completed
    - order.cancelled
    """
    db_subscription = WebhookSubscription(
        url=subscription.url,
        event_type=subscription.event_type,
        is_active=1
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    
    return WebhookSubscriptionResponse.model_validate(db_subscription)

@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
def list_subscriptions(db: Session = Depends(get_db)):
    """List all webhook subscriptions"""
    subscriptions = db.query(WebhookSubscription).all()
    return [WebhookSubscriptionResponse.model_validate(s) for s in subscriptions]

@router.delete("/subscriptions/{subscription_id}")
def unsubscribe_webhook(subscription_id: int, db: Session = Depends(get_db)):
    """Unsubscribe webhook"""
    subscription = db.query(WebhookSubscription).filter(
        WebhookSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db.delete(subscription)
    db.commit()
    return {"message": "Webhook unsubscribed successfully"}

# ============= TEST ENDPOINT =============
# Endpoint này giả lập một external system nhận webhook

@router.post("/receiver/test")
async def webhook_test_receiver(request: Request, payload: Dict[str, Any]):
    """
    Test webhook receiver
    Dùng để test xem webhook có gửi đến đúng không
    
    Trong thực tế, đây là endpoint của hệ thống bên ngoài
    """
    print("=" * 60)
    print("WEBHOOK RECEIVED!")
    print(f"Event Type: {payload.get('event_type')}")
    print(f"Data: {payload.get('data')}")
    print(f"Timestamp: {payload.get('timestamp')}")
    print("=" * 60)
    
    return {
        "status": "success",
        "message": "Webhook received successfully",
        "received_at": payload.get('timestamp')
    }