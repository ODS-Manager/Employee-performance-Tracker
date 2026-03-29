"""
Allowed Duplicate Products API Routes
Manage product types that allow duplicate file numbers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.models.user import User
from app.models.allowed_duplicate_product import AllowedDuplicateProduct
from app.schemas.allowed_duplicate_product import (
    AllowedDuplicateProductCreate,
    AllowedDuplicateProductUpdate,
    AllowedDuplicateProductResponse,
    AllowedDuplicateProductListResponse
)
from app.services.cache_service import cache

router = APIRouter()


def normalize_product_type(product_type: str) -> str:
    """Normalize product type for consistent storage and comparison"""
    return " ".join(product_type.strip().lower().split())


@router.get("", response_model=AllowedDuplicateProductListResponse)
async def list_allowed_duplicate_products(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of product types that allow duplicates.
    Available to all authenticated users.
    """
    items = db.query(AllowedDuplicateProduct).order_by(
        AllowedDuplicateProduct.is_active.desc(),
        AllowedDuplicateProduct.product_type
    ).all()
    
    return {
        "items": items,
        "total": len(items)
    }


@router.post("", response_model=AllowedDuplicateProductResponse, status_code=status.HTTP_201_CREATED)
async def create_allowed_duplicate_product(
    data: AllowedDuplicateProductCreate,
    current_user: User = Depends(require_admin),  # Only admins can create
    db: Session = Depends(get_db)
):
    """
    Add a product type to the allowed duplicates list.
    Requires admin or superadmin role.
    """
    # Normalize the product type
    normalized_product = normalize_product_type(data.product_type)
    
    # Check if already exists
    existing = db.query(AllowedDuplicateProduct).filter(
        AllowedDuplicateProduct.product_type == normalized_product
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product type '{normalized_product}' is already in the allowed duplicates list"
        )
    
    # Create new entry
    allowed_product = AllowedDuplicateProduct(
        product_type=normalized_product,
        is_active=True,
        created_by=current_user.id
    )
    
    db.add(allowed_product)
    db.commit()
    db.refresh(allowed_product)
    
    # Invalidate cache
    cache.delete("allowed_duplicate_products")
    
    return allowed_product


@router.put("/{product_id}", response_model=AllowedDuplicateProductResponse)
async def update_allowed_duplicate_product(
    product_id: int,
    data: AllowedDuplicateProductUpdate,
    current_user: User = Depends(require_admin),  # Only admins can update
    db: Session = Depends(get_db)
):
    """
    Update an allowed duplicate product (typically to toggle is_active).
    Requires admin or superadmin role.
    """
    allowed_product = db.query(AllowedDuplicateProduct).filter(
        AllowedDuplicateProduct.id == product_id
    ).first()
    
    if not allowed_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed duplicate product not found"
        )
    
    # Update fields
    allowed_product.is_active = data.is_active
    allowed_product.modified_by = current_user.id
    
    db.commit()
    db.refresh(allowed_product)
    
    # Invalidate cache
    cache.delete("allowed_duplicate_products")
    
    return allowed_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allowed_duplicate_product(
    product_id: int,
    current_user: User = Depends(require_admin),  # Only admins can delete
    db: Session = Depends(get_db)
):
    """
    Remove a product type from the allowed duplicates list.
    Requires admin or superadmin role.
    """
    allowed_product = db.query(AllowedDuplicateProduct).filter(
        AllowedDuplicateProduct.id == product_id
    ).first()
    
    if not allowed_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed duplicate product not found"
        )
    
    db.delete(allowed_product)
    db.commit()
    
    # Invalidate cache
    cache.delete("allowed_duplicate_products")
    
    return None
