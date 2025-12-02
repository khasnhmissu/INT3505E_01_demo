from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.api import products, orders, webhooks
from app.services.event_bus import event_bus

# Event handlers - Demo Event-Driven Pattern
async def log_order_created(data):
    """Handler 1: Log khi order được tạo"""
    print(f"[Logger Service] 📝 Order created: {data['order_id']}")

async def notify_inventory(data):
    """Handler 2: Thông báo cho inventory service"""
    print(f"[Inventory Service] 📦 Update stock for order: {data['order_id']}")

async def send_email(data):
    """Handler 3: Gửi email cho customer"""
    print(f"[Email Service] 📧 Sending confirmation to: {data['customer_name']}")

async def update_analytics(data):
    """Handler 4: Update analytics"""
    print(f"[Analytics Service] 📊 Recording order: ${data['total_amount']}")

# Lifespan event để setup/cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables & Subscribe event handlers
    print("🚀 Starting up...")
    Base.metadata.create_all(bind=engine)
    
    # Subscribe multiple handlers to same event (Event-Driven Pattern)
    event_bus.subscribe("order.created", log_order_created)
    event_bus.subscribe("order.created", notify_inventory)
    event_bus.subscribe("order.created", send_email)
    event_bus.subscribe("order.created", update_analytics)
    
    print("✓ Database initialized")
    print("✓ Event handlers registered")
    print("-" * 60)
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
    description="""
    ## Order Management API - Demo API Design Patterns
    
    ### Patterns được implement:
    
    1. **CRUD Pattern** (`/products`, `/orders`)
       - Create, Read, Update, Delete operations
       - Resource-centric endpoints
    
    2. **Query Pattern** (`/orders?status=...&sort_by=...`)
       - Filtering: `status`, `customer_name`, `min_amount`, `max_amount`
       - Sorting: `sort_by` & `order_by`
       - Pagination: `skip` & `limit`
    
    3. **HATEOAS Pattern**
       - Mỗi response có `links` object
       - Client biết được actions có thể thực hiện tiếp theo
       - Links thay đổi theo trạng thái resource
    
    4. **Event-Driven Pattern**
       - Internal event bus
       - Multiple subscribers có thể lắng nghe cùng 1 event
       - Async processing, decoupled services
    
    5. **Webhook Pattern** (`/webhooks`)
       - Subscribe/unsubscribe webhooks
       - Automatic HTTP POST notification
       - Event types: `order.created`, `order.completed`, etc.
    
    ### Test flow:
    1. Tạo products: `POST /products`
    2. Subscribe webhook: `POST /webhooks/subscribe`
    3. Tạo order: `POST /orders` → trigger events & webhooks
    4. Query orders: `GET /orders?status=pending&sort_by=created_at`
    5. Process order: `POST /orders/{id}/process`
    6. Complete order: `POST /orders/{id}/complete` → trigger webhook
    """
)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(webhooks.router)

@app.get("/")
def root():
    """Root endpoint với HATEOAS links"""
    return {
        "message": "Order Management API",
        "version": settings.API_VERSION,
        "links": {
            "docs": "/docs",
            "products": "/products",
            "orders": "/orders",
            "webhooks": "/webhooks",
            "webhook_test_receiver": "/webhooks/receiver/test"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)