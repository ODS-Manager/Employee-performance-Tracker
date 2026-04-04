from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class FANameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="FA Name")


class FANameCreate(FANameBase):
    pass


class FANameUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="FA Name")
    is_active: bool = Field(..., description="Active status")


class FAName(FANameBase):
    id: int
    is_active: bool
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class FANameListResponse(BaseModel):
    items: List[FAName]
    total: int
