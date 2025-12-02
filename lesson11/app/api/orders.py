"""
CRUD + Query Pattern + Event-Driven cho Orders
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services.event_bus import event_bus
from app.services.webhook_service import webhook_service

router = APIRouter(prefix="/orders", tags=["Orders - CRUD + Query + Events"])

def add_hateoas_links(request: Request, order: Order) -> dict:
    """HATEOAS Pattern: Client biết được actions có thể thực hiện"""
    base_url = str(request.base_url).rstrip('/')
    links = {
        "self": f"{base_url}/orders/{order.id}",
        "all_orders": f"{base_url}/orders"
    }
    
    # Conditional links dựa trên status
    if order.status == OrderStatus.PENDING:
        links["process"] = f"{base_url}/orders/{order.id}/process"
        links["cancel"] = f"{base_url}/orders/{order.id}/cancel"
    elif order.status == OrderStatus.PROCESSING:
        links["complete"] = f"{base_url}/orders/{order.id}/complete"
        links["cancel"] = f"{base_url}/orders/{order.id}/cancel"
    
    return links

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate, request: Request, db: Session = Depends(get_db)):
    """
    CREATE - Tạo order mới
    Kích hoạt event: order.created
    """
    # Validate product
    product = db.query(Product).filter(Product.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Calculate total
    total = product.price * order.quantity
    
    # Create order
    db_order = Order(
        customer_name=order.customer_name,
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=total,
        status=OrderStatus.PENDING
    )
    db.add(db_order)
    
    # Update stock
    product.stock -= order.quantity
    
    db.commit()
    db.refresh(db_order)
    
    # EVENT-DRIVEN: Publish event
    await event_bus.publish("order.created", {
        "order_id": db_order.id,
        "customer_name": db_order.customer_name,
        "total_amount": db_order.total_amount,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # WEBHOOK: Send notification
    await webhook_service.send_webhook(db, "order.created", {
        "order_id": db_order.id,
        "customer_name": db_order.customer_name,
        "total_amount": db_order.total_amount,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    response = OrderResponse.model_validate(db_order)
    response.links = add_hateoas_links(request, db_order)
    return response

@router.get("/", response_model=List[OrderResponse])
def list_orders(
    request: Request,
    # QUERY PATTERN: Filter, Sort, Pagination
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    min_amount: Optional[float] = Query(None, description="Minimum order amount"),
    max_amount: Optional[float] = Query(None, description="Maximum order amount"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    order_by: Optional[str] = Query("desc", description="asc or desc"),
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(100, description="Pagination limit"),
    db: Session = Depends(get_db)
):
    """
    QUERY PATTERN - List orders với filtering, sorting, pagination
    """
    query = db.query(Order)
    
    # Filters
    if status:
        query = query.filter(Order.status == status)
    if customer_name:
        query = query.filter(Order.customer_name.contains(customer_name))
    if min_amount:
        query = query.filter(Order.total_amount >= min_amount)
    if max_amount:
        query = query.filter(Order.total_amount <= max_amount)
    
    # Sorting
    if hasattr(Order, sort_by):
        order_column = getattr(Order, sort_by)
        if order_by == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Pagination
    orders = query.offset(skip).limit(limit).all()
    
    result = []
    for o in orders:
        order_response = OrderResponse.model_validate(o)
        order_response.links = add_hateoas_links(request, o)
        result.append(order_response)
    
    return result

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """READ - Get single order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    response = OrderResponse.model_validate(order)
    response.links = add_hateoas_links(request, order)
    return response

@router.post("/{order_id}/process", response_model=OrderResponse)
async def process_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Action endpoint: Chuyển order sang trạng thái PROCESSING"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only process pending orders")
    
    order.status = OrderStatus.PROCESSING
    db.commit()
    db.refresh(order)
    
    # EVENT: order.processing
    await event_bus.publish("order.processing", {
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    response = OrderResponse.model_validate(order)
    response.links = add_hateoas_links(request, order)
    return response

@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Action endpoint: Hoàn thành order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Can only complete processing orders")
    
    order.status = OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)
    
    # EVENT: order.completed
    await event_bus.publish("order.completed", {
        "order_id": order.id,
        "total_amount": order.total_amount,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # WEBHOOK: Very important event!
    await webhook_service.send_webhook(db, "order.completed", {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "total_amount": order.total_amount,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    response = OrderResponse.model_validate(order)
    response.links = add_hateoas_links(request, order)
    return response

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Action endpoint: Hủy order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed orders")
    
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Order already cancelled")
    
    # Restore stock
    product = db.query(Product).filter(Product.id == order.product_id).first()
    if product:
        product.stock += order.quantity
    
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    
    # EVENT: order.cancelled
    await event_bus.publish("order.cancelled", {
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    response = OrderResponse.model_validate(order)
    response.links = add_hateoas_links(request, order)
    return response