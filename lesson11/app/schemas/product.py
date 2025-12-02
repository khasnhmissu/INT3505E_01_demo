from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    
    # HATEOAS: Thêm links để client biết actions có thể thực hiện
    links: Optional[dict] = None
    
    class Config:
        from_attributes = True