"""
Webhook Service - Gửi HTTP POST đến các URL đã đăng ký
"""
import httpx
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.models.order import WebhookSubscription

class WebhookService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send_webhook(self, db: Session, event_type: str, payload: Dict[str, Any]):
        """
        Gửi webhook đến tất cả subscribers của event_type
        Retry logic có thể thêm ở đây
        """
        subscriptions = db.query(WebhookSubscription).filter(
            WebhookSubscription.event_type == event_type,
            WebhookSubscription.is_active == 1
        ).all()
        
        if not subscriptions:
            print(f"⚠ No webhook subscriptions for {event_type}")
            return
        
        for subscription in subscriptions:
            try:
                print(f"Sending webhook to {subscription.url}")
                response = await self.client.post(
                    subscription.url,
                    json={
                        "event_type": event_type,
                        "data": payload,
                        "timestamp": payload.get("timestamp")
                    }
                )
                
                if response.status_code == 200:
                    print(f"Webhook delivered successfully to {subscription.url}")
                else:
                    print(f"Webhook failed: {response.status_code} - {subscription.url}")
                    
            except Exception as e:
                print(f"Webhook error to {subscription.url}: {str(e)}")
                # Trong production: retry logic, dead letter queue, etc.
    
    async def close(self):
        await self.client.aclose()

webhook_service = WebhookService()