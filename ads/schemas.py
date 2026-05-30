"""
Pydantic schemas for the Ads service
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AdCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    priority: int = Field(0, ge=0)


class AdUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


class AdResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    url: Optional[str]
    image_url: Optional[str]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
