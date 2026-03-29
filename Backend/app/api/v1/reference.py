"""
Reference Tables API Routes
CRUD operations for lookup/configuration tables
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.core.dependencies import (
    get_current_active_user, require_admin,
    ROLE_SUPERADMIN, ROLE_ADMIN
)
from app.models.user import User
from app.models.reference import TransactionType, ProcessType, OrderStatusType, Division, PropertyType
from app.models.team import TeamProduct, TeamState
from app.services.cache_service import cache

router = APIRouter()


def ensure_reference_defaults(db: Session, reference_type: str) -> None:
    """Seed default reference data when a reference table is empty."""
    items_to_add = []

    if reference_type == "transaction_types":
        if db.query(TransactionType.id).first() is None:
            defaults = [
                "Sale/Cash",
                "Sale w/Mortgage",
                "Refinance",
                "HELOC",
                "Commercial",
            ]
            items_to_add = [TransactionType(name=name, is_active=True) for name in defaults]

    elif reference_type == "process_types":
        if db.query(ProcessType.id).first() is None:
            defaults = ["Step1", "Step2", "Single Seat"]
            items_to_add = [ProcessType(name=name, is_active=True) for name in defaults]

    elif reference_type == "order_statuses":
        if db.query(OrderStatusType.id).first() is None:
            defaults = ["Completed", "On-hold", "BP & RTI", "In Progress"]
            items_to_add = [OrderStatusType(name=name, is_active=True) for name in defaults]

    elif reference_type == "divisions":
        if db.query(Division.id).first() is None:
            defaults = [
                ("Direct", "Direct business"),
                ("Agency", "Agency business"),
            ]
            items_to_add = [Division(name=name, description=description) for name, description in defaults]

    elif reference_type == "property_types":
        if db.query(PropertyType.id).first() is None:
            defaults = ["Residential", "HSD", "Commercial"]
            items_to_add = [PropertyType(name=name, is_active=True) for name in defaults]

    if not items_to_add:
        return

    db.add_all(items_to_add)
    db.commit()
    cache.invalidate_reference_cache(reference_type)


def serialize_transaction_type(item):
    return {
        "id": item.id,
        "name": item.name,
        "isActive": item.is_active,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "modifiedAt": item.modified_at.isoformat() if item.modified_at else None
    }


def serialize_process_type(item):
    return {
        "id": item.id,
        "name": item.name,
        "isActive": item.is_active,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "modifiedAt": item.modified_at.isoformat() if item.modified_at else None
    }


def serialize_order_status(item):
    return {
        "id": item.id,
        "name": item.name,
        "isActive": item.is_active,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "modifiedAt": item.modified_at.isoformat() if item.modified_at else None
    }


def serialize_division(item):
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "modifiedAt": item.modified_at.isoformat() if item.modified_at else None
    }


# ============ Transaction Types ============
@router.get("/transaction-types")
async def list_transaction_types(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all transaction types"""
    ensure_reference_defaults(db, "transaction_types")

    # Check cache first
    cached_data = cache.get_reference("transaction_types", is_active)
    if cached_data is not None:
        return cached_data
    
    query = db.query(TransactionType)
    if is_active is not None:
        query = query.filter(TransactionType.is_active == is_active)
    
    result = [serialize_transaction_type(t) for t in query.order_by(TransactionType.name).all()]
    
    # Cache the result
    cache.set_reference("transaction_types", result, is_active)
    return result


@router.get("/transaction-types/{type_id}")
async def get_transaction_type(
    type_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transaction type by ID"""
    item = db.query(TransactionType).filter(TransactionType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction type not found")
    return serialize_transaction_type(item)


@router.post("/transaction-types", status_code=status.HTTP_201_CREATED)
async def create_transaction_type(
    name: str = Body(...),
    is_active: bool = Body(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new transaction type (Admin or Superadmin only)"""
    existing = db.query(TransactionType).filter(TransactionType.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction type name already exists")
    
    item = TransactionType(name=name, is_active=is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("transaction_types")
    return serialize_transaction_type(item)


@router.put("/transaction-types/{type_id}")
async def update_transaction_type(
    type_id: int,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update transaction type (Admin or Superadmin only)"""
    item = db.query(TransactionType).filter(TransactionType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction type not found")
    
    if name is not None:
        existing = db.query(TransactionType).filter(
            TransactionType.name == name,
            TransactionType.id != type_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction type name already exists")
        item.name = name
    
    if is_active is not None:
        item.is_active = is_active
    
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("transaction_types")
    return serialize_transaction_type(item)


@router.delete("/transaction-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_type(
    type_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate transaction type (Admin or Superadmin only)"""
    item = db.query(TransactionType).filter(TransactionType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction type not found")
    
    item.is_active = False
    db.commit()
    
    # Invalidate cache
    cache.invalidate_reference_cache("transaction_types")


# ============ Process Types ============
@router.get("/process-types")
async def list_process_types(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all process types"""
    ensure_reference_defaults(db, "process_types")

    # Check cache first
    cached_data = cache.get_reference("process_types", is_active)
    if cached_data is not None:
        return cached_data
    
    query = db.query(ProcessType)
    if is_active is not None:
        query = query.filter(ProcessType.is_active == is_active)
    
    result = [serialize_process_type(t) for t in query.order_by(ProcessType.name).all()]
    
    # Cache the result
    cache.set_reference("process_types", result, is_active)
    return result


@router.get("/process-types/{type_id}")
async def get_process_type(
    type_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get process type by ID"""
    item = db.query(ProcessType).filter(ProcessType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process type not found")
    return serialize_process_type(item)


@router.post("/process-types", status_code=status.HTTP_201_CREATED)
async def create_process_type(
    name: str = Body(...),
    is_active: bool = Body(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new process type (Admin or Superadmin only)"""
    existing = db.query(ProcessType).filter(ProcessType.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Process type name already exists")
    
    item = ProcessType(name=name, is_active=is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("process_types")
    return serialize_process_type(item)


@router.put("/process-types/{type_id}")
async def update_process_type(
    type_id: int,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update process type (Admin or Superadmin only)"""
    item = db.query(ProcessType).filter(ProcessType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process type not found")
    
    if name is not None:
        existing = db.query(ProcessType).filter(
            ProcessType.name == name,
            ProcessType.id != type_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Process type name already exists")
        item.name = name
    
    if is_active is not None:
        item.is_active = is_active
    
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("process_types")
    return serialize_process_type(item)


@router.delete("/process-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process_type(
    type_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate process type (Admin or Superadmin only)"""
    item = db.query(ProcessType).filter(ProcessType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process type not found")
    
    item.is_active = False
    db.commit()
    
    # Invalidate cache
    cache.invalidate_reference_cache("process_types")


# ============ Order Status Types ============
@router.get("/order-statuses")
async def list_order_statuses(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all order status types"""
    ensure_reference_defaults(db, "order_statuses")

    # Check cache first
    cached_data = cache.get_reference("order_statuses", is_active)
    if cached_data is not None:
        return cached_data
    
    query = db.query(OrderStatusType)
    if is_active is not None:
        query = query.filter(OrderStatusType.is_active == is_active)
    
    result = [serialize_order_status(t) for t in query.order_by(OrderStatusType.name).all()]
    
    # Cache the result
    cache.set_reference("order_statuses", result, is_active)
    return result


@router.get("/order-statuses/{status_id}")
async def get_order_status(
    status_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get order status by ID"""
    item = db.query(OrderStatusType).filter(OrderStatusType.id == status_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order status not found")
    return serialize_order_status(item)


@router.post("/order-statuses", status_code=status.HTTP_201_CREATED)
async def create_order_status(
    name: str = Body(...),
    is_active: bool = Body(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new order status (Admin or Superadmin only)"""
    existing = db.query(OrderStatusType).filter(OrderStatusType.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order status name already exists")
    
    item = OrderStatusType(name=name, is_active=is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("order_statuses")
    return serialize_order_status(item)


@router.put("/order-statuses/{status_id}")
async def update_order_status(
    status_id: int,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update order status (Admin or Superadmin only)"""
    item = db.query(OrderStatusType).filter(OrderStatusType.id == status_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order status not found")
    
    if name is not None:
        existing = db.query(OrderStatusType).filter(
            OrderStatusType.name == name,
            OrderStatusType.id != status_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order status name already exists")
        item.name = name
    
    if is_active is not None:
        item.is_active = is_active
    
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("order_statuses")
    return serialize_order_status(item)


@router.delete("/order-statuses/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_status(
    status_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate order status (Admin or Superadmin only)"""
    item = db.query(OrderStatusType).filter(OrderStatusType.id == status_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order status not found")
    
    item.is_active = False
    db.commit()
    
    # Invalidate cache
    cache.invalidate_reference_cache("order_statuses")


# ============ Divisions ============
@router.get("/divisions")
async def list_divisions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all divisions"""
    ensure_reference_defaults(db, "divisions")

    # Check cache first
    cached_data = cache.get_reference("divisions", None)
    if cached_data is not None:
        return cached_data
    
    result = [serialize_division(d) for d in db.query(Division).order_by(Division.name).all()]
    
    # Cache the result
    cache.set_reference("divisions", result, None)
    return result


@router.get("/divisions/{division_id}")
async def get_division(
    division_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get division by ID"""
    item = db.query(Division).filter(Division.id == division_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    return serialize_division(item)


@router.post("/divisions", status_code=status.HTTP_201_CREATED)
async def create_division(
    name: str = Body(...),
    description: str = Body(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new division (Admin or Superadmin only)"""
    existing = db.query(Division).filter(Division.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Division name already exists")
    
    item = Division(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("divisions")
    return serialize_division(item)


@router.put("/divisions/{division_id}")
async def update_division(
    division_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update division (Admin or Superadmin only)"""
    item = db.query(Division).filter(Division.id == division_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    
    if name is not None:
        existing = db.query(Division).filter(
            Division.name == name,
            Division.id != division_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Division name already exists")
        item.name = name
    
    if description is not None:
        item.description = description
    
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("divisions")
    return serialize_division(item)


@router.delete("/divisions/{division_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_division(
    division_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete division (Admin or Superadmin only)"""
    item = db.query(Division).filter(Division.id == division_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    
    db.delete(item)
    db.commit()
    
    # Invalidate cache
    cache.invalidate_reference_cache("divisions")


# ============ Property Types CRUD ============
def serialize_property_type(item):
    return {
        "id": item.id,
        "name": item.name,
        "isActive": item.is_active,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "modifiedAt": item.modified_at.isoformat() if item.modified_at else None
    }


@router.get("/property-types")
async def list_property_types(
    active_only: bool = Query(True, description="Filter only active property types"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all property types"""
    ensure_reference_defaults(db, "property_types")
    
    query = db.query(PropertyType)
    if active_only:
        query = query.filter(PropertyType.is_active == True)
    
    items = query.order_by(PropertyType.name).all()
    return [serialize_property_type(item) for item in items]


@router.get("/property-types/{property_type_id}")
async def get_property_type(
    property_type_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get property type by ID"""
    item = db.query(PropertyType).filter(PropertyType.id == property_type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property type not found")
    return serialize_property_type(item)


@router.post("/property-types", status_code=status.HTTP_201_CREATED)
async def create_property_type(
    name: str = Body(...),
    is_active: bool = Body(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new property type (Admin or Superadmin only)"""
    existing = db.query(PropertyType).filter(PropertyType.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property type name already exists")
    
    item = PropertyType(name=name, is_active=is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("property_types")
    return serialize_property_type(item)


@router.put("/property-types/{property_type_id}")
async def update_property_type(
    property_type_id: int,
    name: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update property type (Admin or Superadmin only)"""
    item = db.query(PropertyType).filter(PropertyType.id == property_type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property type not found")
    
    if name is not None:
        existing = db.query(PropertyType).filter(
            PropertyType.name == name,
            PropertyType.id != property_type_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property type name already exists")
        item.name = name
    
    if is_active is not None:
        item.is_active = is_active
    
    db.commit()
    db.refresh(item)
    
    # Invalidate cache
    cache.invalidate_reference_cache("property_types")
    return serialize_property_type(item)


@router.delete("/property-types/{property_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_type(
    property_type_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Soft delete property type (set is_active to False)"""
    item = db.query(PropertyType).filter(PropertyType.id == property_type_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property type not found")
    
    item.is_active = False
    db.commit()
    
    # Invalidate cache
    cache.invalidate_reference_cache("property_types")


# ============ Product Types (from team_products) ============
@router.get("/product-types")
async def list_product_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all unique product types from team_products table"""
    # Get distinct product types
    products = db.query(TeamProduct.product_type).distinct().all()
    product_types = [{"id": i+1, "name": p[0], "isActive": True} for i, p in enumerate(products)]
    return sorted(product_types, key=lambda x: x["name"])


@router.post("/product-types", status_code=status.HTTP_201_CREATED)
async def create_product_type(
    name: str = Body(...),
    team_id: int = Body(1),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new product type - saves to team_products table"""
    existing = db.query(TeamProduct).filter(
        TeamProduct.product_type == name,
        TeamProduct.team_id == team_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product type already exists in team_products")
    
    new_product = TeamProduct(team_id=team_id, product_type=name)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {"id": new_product.id, "name": name, "isActive": True}


# ============ States (from team_states) ============
@router.get("/states")
async def list_states(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all unique states from team_states table"""
    # Get distinct states
    states = db.query(TeamState.state).distinct().all()
    state_list = [{"id": i+1, "code": s[0], "name": s[0], "isActive": True} for i, s in enumerate(states)]
    return sorted(state_list, key=lambda x: x["code"])


@router.post("/states", status_code=status.HTTP_201_CREATED)
async def create_state(
    code: str = Body(...),
    name: str = Body(None),
    team_id: int = Body(1),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new state - saves to team_states table"""
    existing = db.query(TeamState).filter(
        TeamState.state == code,
        TeamState.team_id == team_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State already exists in team_states")
    
    new_state = TeamState(team_id=team_id, state=code)
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    
    return {"id": new_state.id, "code": code, "name": name or code, "isActive": True}
