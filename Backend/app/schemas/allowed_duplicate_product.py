"""
Allowed Duplicate Product Schemas
Pydantic schemas for managing product types that allow duplicates
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AllowedDuplicateProductBase(BaseModel):
    product_type: str = Field(..., max_length=100, alias="productType")


class AllowedDuplicateProductCreate(AllowedDuplicateProductBase):
    """Schema for creating a new allowed duplicate product type"""
    pass


class AllowedDuplicateProductUpdate(BaseModel):
    """Schema for updating an allowed duplicate product type"""
    is_active: bool = Field(..., alias="isActive")
    
    class Config:
        populate_by_name = True


class AllowedDuplicateProductResponse(AllowedDuplicateProductBase):
    """Schema for allowed duplicate product response"""
    id: int
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    created_by: int = Field(..., alias="createdBy")
    modified_at: Optional[datetime] = Field(None, alias="modifiedAt")
    modified_by: Optional[int] = Field(None, alias="modifiedBy")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class AllowedDuplicateProductListResponse(BaseModel):
    """Schema for list of allowed duplicate products"""
    items: list[AllowedDuplicateProductResponse]
    total: int
