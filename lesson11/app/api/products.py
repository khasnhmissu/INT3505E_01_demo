"""
CRUD Pattern cho Products
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products - CRUD"])

def add_hateoas_links(request: Request, product: Product) -> dict:
    """HATEOAS Pattern: Thêm links cho client"""
    base_url = str(request.base_url).rstrip('/')
    return {
        "self": f"{base_url}/products/{product.id}",
        "update": f"{base_url}/products/{product.id}",
        "delete": f"{base_url}/products/{product.id}",
        "all_products": f"{base_url}/products"
    }

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, request: Request, db: Session = Depends(get_db)):
    """CREATE - Tạo product mới"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # HATEOAS: Thêm links
    response = ProductResponse.model_validate(db_product)
    response.links = add_hateoas_links(request, db_product)
    return response

@router.get("/", response_model=List[ProductResponse])
def list_products(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """READ - List tất cả products"""
    products = db.query(Product).offset(skip).limit(limit).all()
    
    # HATEOAS cho mỗi product
    result = []
    for p in products:
        product_response = ProductResponse.model_validate(p)
        product_response.links = add_hateoas_links(request, p)
        result.append(product_response)
    
    return result

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    """READ - Lấy 1 product theo ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    response = ProductResponse.model_validate(product)
    response.links = add_hateoas_links(request, product)
    return response

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """UPDATE - Cập nhật product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    response = ProductResponse.model_validate(product)
    response.links = add_hateoas_links(request, product)
    return response

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """DELETE - Xóa product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}