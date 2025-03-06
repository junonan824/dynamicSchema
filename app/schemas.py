from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DynamicColumnsBase(BaseModel):
    name: str
    data: Dict[str, Any] = {}

class DynamicColumnsCreate(DynamicColumnsBase):
    pass

class DynamicColumnsUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class DynamicColumns(DynamicColumnsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 