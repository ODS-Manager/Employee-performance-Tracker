"""
Orders API Routes
CRUD operations for order management with step-based workflow
"""
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, datetime
from app.database import get_db
from app.core.dependencies import (
    get_current_active_user, require_admin, require_team_lead,
    check_org_access, check_team_access, get_user_teams,
    ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD, ROLE_EXAMINER
)
from app.models.user import User
from app.models.order import Order
from app.models.order_history import OrderHistory
from app.models.team import Team
from app.models.user_team import UserTeam
from app.models.reference import OrderStatusType
from app.models.fa_name import FAName
from app.models.allowed_duplicate_product import AllowedDuplicateProduct
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.cache_service import cache

logger = logging.getLogger(__name__)

router = APIRouter()


def normalize_product_type(product_type: Optional[str]) -> str:
    """Normalize product type values for reliable comparisons."""
    if not product_type:
        return ""
    return " ".join(product_type.strip().lower().split())


def is_duplicate_allowed_product(product_type: Optional[str], db: Session) -> bool:
    """
    Return True when duplicates are allowed for the given product type.
    Checks the database instead of hardcoded list.
    """
    # Check cache first
    cache_key = f"allowed_dup_product:{normalize_product_type(product_type)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    normalized = normalize_product_type(product_type)
    if not normalized:
        cache.set(cache_key, False, ttl=300)  # Cache for 5 minutes
        return False
    
    # Query database
    result = db.query(AllowedDuplicateProduct).filter(
        AllowedDuplicateProduct.product_type == normalized,
        AllowedDuplicateProduct.is_active == True
    ).first()
    
    is_allowed = result is not None
    cache.set(cache_key, is_allowed, ttl=300)  # Cache for 5 minutes
    return is_allowed


def can_create_duplicate_for_product(user: User, product_type: Optional[str], db: Session) -> bool:
    role = user.user_role.lower() if user.user_role else ""

    # Admins and superadmins can create duplicates for all product types.
    if role in {ROLE_SUPERADMIN, ROLE_ADMIN}:
        return True

    # Team leads and examiners can create duplicates only for configured product types.
    if not is_duplicate_allowed_product(product_type, db):
        return False

    return role in {ROLE_TEAM_LEAD, ROLE_EXAMINER}


# ============ Serializer Functions ============

def serialize_step_info(order, step_num: int) -> Optional[dict]:
    """Serialize step information to camelCase dict"""
    try:
        if step_num == 1:
            user_id = order.step1_user_id
            user = order.step1_user if hasattr(order, 'step1_user') else None
            fa_name_obj = order.step1_fa_name if hasattr(order, 'step1_fa_name') else None
            fa_name = fa_name_obj.name if fa_name_obj else None
            fa_name_id = order.step1_fa_name_id
        else:
            user_id = order.step2_user_id
            user = order.step2_user if hasattr(order, 'step2_user') else None
            fa_name_obj = order.step2_fa_name if hasattr(order, 'step2_fa_name') else None
            fa_name = fa_name_obj.name if fa_name_obj else None
            fa_name_id = order.step2_fa_name_id
        
        if not user_id:
            return None
        
        return {
            "userId": user_id,
            "userName": user.user_name if user else None,
            "employeeId": user.employee_id if user else None,
            "faName": fa_name,
            "faNameId": fa_name_id
        }
    except Exception as e:
        logger.error(f"Error serializing step {step_num} for order {order.id}: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a safe fallback
        return {
            "userId": order.step1_user_id if step_num == 1 else order.step2_user_id,
            "userName": None,
            "employeeId": None,
            "faName": None,
            "faNameId": order.step1_fa_name_id if step_num == 1 else order.step2_fa_name_id
        }


def serialize_reference_type(ref_obj) -> Optional[dict]:
    """Serialize reference type (transaction type, process type, etc.) to dict"""
    if not ref_obj:
        return None
    return {
        "id": ref_obj.id,
        "name": ref_obj.name
    }


def serialize_order(order: Order, include_steps: bool = True) -> dict:
    """Serialize order to camelCase dict"""
    try:
        # Get the process type name for display
        effective_process_type_name = order.process_type.name if order.process_type else "Unknown"
        
        # Create a modified process type object for display
        process_type_display = None
        if hasattr(order, 'process_type') and order.process_type:
            process_type_display = {
                "id": order.process_type.id,
                "name": effective_process_type_name  # Use effective name instead of original
            }
        
        result = {
            "id": order.id,
            "fileNumber": order.file_number,
            "entryDate": order.entry_date.isoformat() if order.entry_date else None,
            "transactionTypeId": order.transaction_type_id,
            "transactionType": serialize_reference_type(order.transaction_type) if hasattr(order, 'transaction_type') else None,
            "processTypeId": order.process_type_id,
            "processType": process_type_display,  # Use the modified process type with effective name
            "orderStatusId": order.order_status_id,
            "orderStatus": serialize_reference_type(order.order_status) if hasattr(order, 'order_status') else None,
            "divisionId": order.division_id,
            "division": serialize_reference_type(order.division) if hasattr(order, 'division') else None,
            "propertyTypeId": order.property_type_id,
            "propertyType": serialize_reference_type(order.property_type) if hasattr(order, 'property_type') and order.property_type else None,
            "state": order.state,
            "county": order.county,
            "productType": order.product_type,
            "productionType": order.production_type or "regular",  # Default to 'regular' if NULL
            "teamId": order.team_id,
            "orgId": order.org_id,
            "billingStatus": order.billing_status or "pending",  # Default to 'pending' if NULL
            "createdBy": order.created_by,
            "modifiedBy": order.modified_by,
            "createdAt": order.created_at.isoformat() if order.created_at else None,
            "modifiedAt": order.modified_at.isoformat() if order.modified_at else None,
            "deletedAt": order.deleted_at.isoformat() if order.deleted_at else None,
            "deletedBy": order.deleted_by
        }
        
        if include_steps:
            result["step1"] = serialize_step_info(order, 1)
            result["step2"] = serialize_step_info(order, 2)
        
        return result
    except Exception as e:
        logger.error(f"Error serializing order {order.id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def serialize_simple_order(order: Order) -> dict:
    """Serialize order to simplified camelCase dict for lists"""
    # Get the process type name for display
    effective_process_type_name = order.process_type.name if order.process_type else "Unknown"
    
    return {
        "id": order.id,
        "fileNumber": order.file_number,
        "entryDate": order.entry_date.isoformat() if order.entry_date else None,
        "state": order.state,
        "county": order.county,
        "productType": order.product_type,
        "productionType": order.production_type or "regular",  # Default to 'regular' if NULL
        "transactionTypeName": order.transaction_type.name if order.transaction_type else None,
        "processTypeName": effective_process_type_name,  # Use effective name instead of original
        "orderStatusName": order.order_status.name if order.order_status else None,
        "divisionName": order.division.name if order.division else None,
        "propertyTypeName": order.property_type.name if order.property_type else None,
        "teamId": order.team_id,
        "billingStatus": order.billing_status or "pending",  # Default to 'pending' if NULL
        "createdAt": order.created_at.isoformat() if order.created_at else None,
        "modifiedAt": order.modified_at.isoformat() if order.modified_at else None,
        # Step user IDs for productivity calculation
        "step1UserId": order.step1_user_id,
        "step2UserId": order.step2_user_id,
        # Step usernames for display
        "step1UserName": order.step1_user.user_name if order.step1_user else None,
        "step2UserName": order.step2_user.user_name if order.step2_user else None
    }


def serialize_order_history(h: OrderHistory) -> dict:
    """Serialize order history to camelCase dict"""
    return {
        "id": h.id,
        "orderId": h.order_id,
        "changedBy": h.changed_by,
        "changedByName": h.changed_by_user.user_name if h.changed_by_user else None,
        "fieldName": h.field_name,
        "oldValue": h.old_value,
        "newValue": h.new_value,
        "changeType": h.change_type,
        "changedAt": h.changed_at.isoformat() if h.changed_at else None
    }


def log_order_change(
    db: Session,
    order_id: int,
    changed_by: int,
    field_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
    change_type: str
):
    """Log a change to the order history"""
    history = OrderHistory(
        order_id=order_id,
        changed_by=changed_by,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        change_type=change_type
    )
    db.add(history)


def validate_user_for_step_assignment(
    db: Session,
    user_id: int,
    team_id: int,
    step_name: str,
    allow_non_team_member: bool = False,
) -> None:
    """
    Validate that a user can be assigned to an order step.
    Checks:
    1. User exists
    2. User is globally active (not resigned/deactivated from the system)
    3. User is an active member of the specific team (team-level membership status)
    
    Note: A user can be inactive in one team but active in others.
    The team membership tracks join/leave dates for historical records.
    
    Raises HTTPException if validation fails.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found for {step_name}"
        )
    
    # Check if user is globally active (not resigned from company)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign user '{user.user_name}' to {step_name}. User has resigned or been deactivated from the system."
        )

    # Admin/superadmin override: allow assignment even if user is not in this team
    if allow_non_team_member:
        return
    
    # Check if user is an active member of this specific team
    # A user can be removed from one team but still active in others
    user_team = db.query(UserTeam).filter(
        UserTeam.user_id == user_id,
        UserTeam.team_id == team_id
    ).first()
    
    if not user_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign user '{user.user_name}' to {step_name}. User has never been a member of this team."
        )
    
    if not user_team.is_active:
        # User was removed from this specific team
        left_date = user_team.left_at.strftime("%Y-%m-%d") if user_team.left_at else "unknown date"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign user '{user.user_name}' to {step_name}. User was removed from this team on {left_date}."
        )


def get_matching_orders(
    db: Session,
    file_number: str,
    product_type: str,
    team_id: int,
    exclude_order_id: Optional[int] = None,
) -> List[Order]:
    """Return active orders that share the file/product/team identity."""
    query = db.query(Order).options(
        joinedload(Order.step1_user),
        joinedload(Order.step2_user),
        joinedload(Order.process_type)
    ).filter(
        Order.file_number == file_number,
        Order.product_type == product_type,
        Order.team_id == team_id,
        Order.deleted_at == None
    )

    if exclude_order_id is not None:
        query = query.filter(Order.id != exclude_order_id)

    return query.order_by(Order.modified_at.desc(), Order.id.desc()).all()


def can_merge_requested_steps(
    order: Order,
    adding_step1: bool,
    adding_step2: bool,
    requested_process_type_name: Optional[str],
) -> bool:
    """
    Check whether the requested step can fill the missing half of an existing order.

    Duplicate-enabled products still use this path first; duplicate rows are only
    created when no compatible partial order exists.
    """
    if order.billing_status == "done":
        return False

    # A Single Seat submission represents both steps by one examiner and should
    # not be merged into an existing partial two-person workflow.
    if requested_process_type_name == "Single Seat":
        return False

    # Only one missing step can be merged at a time.
    if adding_step1 == adding_step2:
        return False

    if adding_step1:
        return order.step1_user_id is None and order.step2_user_id is not None

    return order.step2_user_id is None and order.step1_user_id is not None


def find_merge_candidate(
    orders: List[Order],
    adding_step1: bool,
    adding_step2: bool,
    requested_process_type_name: Optional[str],
) -> Optional[Order]:
    """Find the best existing partial order that can accept the requested step."""
    for order in orders:
        if can_merge_requested_steps(order, adding_step1, adding_step2, requested_process_type_name):
            return order
    return None


def find_available_step_candidate(orders: List[Order]) -> Optional[dict]:
    """
    Find any partial order with one available complementary step for the frontend
    file-number pre-check endpoint.
    """
    for order in orders:
        if can_merge_requested_steps(order, False, True, "Step2"):
            return {"order": order, "canAddStep1": False, "canAddStep2": True}
        if can_merge_requested_steps(order, True, False, "Step1"):
            return {"order": order, "canAddStep1": True, "canAddStep2": False}
    return None


def apply_step_merge(
    db: Session,
    existing: Order,
    current_user_id: int,
    step1_user_id: Optional[int] = None,
    step1_fa_name_id: Optional[int] = None,
    step2_user_id: Optional[int] = None,
    step2_fa_name_id: Optional[int] = None,
) -> None:
    """Merge provided step data into an existing partial order with audit logs."""
    if existing.billing_status == "done":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order billing is completed — editing is locked"
        )

    if step1_user_id is not None:
        if existing.step1_user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Step 1 is already completed for this file"
            )
        log_order_change(
            db, existing.id, current_user_id, "step1_user_id",
            str(existing.step1_user_id) if existing.step1_user_id else None,
            str(step1_user_id), "update"
        )
        existing.step1_user_id = step1_user_id

        if step1_fa_name_id is not None:
            log_order_change(
                db, existing.id, current_user_id, "step1_fa_name_id",
                str(existing.step1_fa_name_id) if existing.step1_fa_name_id else None,
                str(step1_fa_name_id), "update"
            )
            existing.step1_fa_name_id = step1_fa_name_id

    if step2_user_id is not None:
        if existing.step2_user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Step 2 is already completed for this file"
            )
        log_order_change(
            db, existing.id, current_user_id, "step2_user_id",
            str(existing.step2_user_id) if existing.step2_user_id else None,
            str(step2_user_id), "update"
        )
        existing.step2_user_id = step2_user_id

        if step2_fa_name_id is not None:
            log_order_change(
                db, existing.id, current_user_id, "step2_fa_name_id",
                str(existing.step2_fa_name_id) if existing.step2_fa_name_id else None,
                str(step2_fa_name_id), "update"
            )
            existing.step2_fa_name_id = step2_fa_name_id

    existing.modified_by = current_user_id


# ============ Routes ============

@router.get("")
async def list_orders(
    org_id: Optional[int] = Query(None, alias="orgId", description="Filter by organization"),
    team_id: Optional[int] = Query(None, alias="teamId", description="Filter by team"),
    order_status_id: Optional[int] = Query(None, alias="orderStatusId", description="Filter by status"),
    order_status_ids: Optional[List[int]] = Query(None, alias="orderStatusIds", description="Filter by multiple statuses"),
    step1_user_id: Optional[int] = Query(None, alias="step1UserId", description="Filter by step1 user"),
    step2_user_id: Optional[int] = Query(None, alias="step2UserId", description="Filter by step2 user"),
    my_orders: bool = Query(False, alias="myOrders", description="Filter orders where current user worked on step1 OR step2"),
    process_type_id: Optional[int] = Query(None, alias="processTypeId", description="Filter by process type"),
    process_type_ids: Optional[List[int]] = Query(None, alias="processTypeIds", description="Filter by multiple process types"),
    division_id: Optional[int] = Query(None, alias="divisionId", description="Filter by division"),
    division_ids: Optional[List[int]] = Query(None, alias="divisionIds", description="Filter by multiple divisions"),
    billing_status: Optional[str] = Query(None, alias="billingStatus", description="Filter by billing status"),
    billing_statuses: Optional[List[str]] = Query(None, alias="billingStatuses", description="Filter by multiple billing statuses"),
    state: Optional[str] = Query(None, description="Filter by state"),
    states: Optional[List[str]] = Query(None, description="Filter by multiple states"),
    search: Optional[str] = Query(None, alias="search", description="Search by file number, state, county, status, or product"),
    fa_name: Optional[str] = Query(None, alias="faName", description="Filter by FA name (step1 or step2)"),
    fa_names: Optional[List[str]] = Query(None, alias="faNames", description="Filter by multiple FA names (step1 or step2)"),
    start_date: Optional[date] = Query(None, alias="startDate", description="Filter by entry date start"),
    end_date: Optional[date] = Query(None, alias="endDate", description="Filter by entry date end"),
    include_deleted: bool = Query(False, alias="includeDeleted", description="Include soft-deleted orders"),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=100000, alias="pageSize"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List orders with filtering based on role"""
    from sqlalchemy import or_
    
    # Build cache key based on user role and filters
    cache_key = cache._build_key(
        cache.PREFIX_ORDERS,
        "list",
        f"role:{current_user.user_role}",
        f"user:{current_user.id}",
        f"org:{org_id}" if org_id else None,
        f"team:{team_id}" if team_id else None,
        f"status:{order_status_id}" if order_status_id else None,
        f"statuses:{','.join(map(str, order_status_ids))}" if order_status_ids else None,
        f"step1:{step1_user_id}" if step1_user_id else None,
        f"step2:{step2_user_id}" if step2_user_id else None,
        f"my:{my_orders}" if my_orders else None,
        f"proc:{process_type_id}" if process_type_id else None,
        f"procs:{','.join(map(str, process_type_ids))}" if process_type_ids else None,
        f"div:{division_id}" if division_id else None,
        f"divs:{','.join(map(str, division_ids))}" if division_ids else None,
        f"bill:{billing_status}" if billing_status else None,
        f"bills:{','.join(billing_statuses)}" if billing_statuses else None,
        f"state:{state}" if state else None,
        f"states:{','.join(states)}" if states else None,
        f"search:{search}" if search else None,
        f"fa:{fa_name}" if fa_name else None,
        f"fas:{','.join(fa_names)}" if fa_names else None,
        f"start:{start_date}" if start_date else None,
        f"end:{end_date}" if end_date else None,
        f"del:{include_deleted}" if include_deleted else None,
        f"page:{page}",
        f"size:{page_size}"
    )
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    query = db.query(Order).options(
        joinedload(Order.transaction_type),
        joinedload(Order.process_type),
        joinedload(Order.order_status),
        joinedload(Order.division)
    )
    
    # Exclude soft-deleted by default
    if not include_deleted:
        query = query.filter(Order.deleted_at == None)
    
    # Apply role-based filtering
    if current_user.user_role.lower() == ROLE_SUPERADMIN:
        if org_id:
            query = query.filter(Order.org_id == org_id)
    elif current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(Order.org_id == current_user.org_id)
    elif current_user.user_role.lower() == ROLE_TEAM_LEAD:
        # Team leads see orders from teams they lead or are members of
        accessible_teams = get_user_teams(current_user, db)
        if not accessible_teams:
            return {"items": [], "total": 0}
        query = query.filter(Order.team_id.in_(accessible_teams))
    else:  # Employee
        # Employees see ALL orders from teams they are members of
        # This allows them to view team orders and add their step to existing files
        accessible_teams = get_user_teams(current_user, db)
        if not accessible_teams:
            return {"items": [], "total": 0}
        query = query.filter(Order.team_id.in_(accessible_teams))
    
    # Apply additional filters
    if team_id:
        query = query.filter(Order.team_id == team_id)
    if order_status_ids:
        query = query.filter(Order.order_status_id.in_(order_status_ids))
    elif order_status_id:
        query = query.filter(Order.order_status_id == order_status_id)
    
    # myOrders filter - show orders where user worked on step1 OR step2
    if my_orders:
        query = query.filter(
            or_(
                Order.step1_user_id == current_user.id,
                Order.step2_user_id == current_user.id
            )
        )
    else:
        # Individual step filters (only apply if myOrders is not set)
        if step1_user_id:
            query = query.filter(Order.step1_user_id == step1_user_id)
        if step2_user_id:
            query = query.filter(Order.step2_user_id == step2_user_id)
    
    if billing_statuses:
        query = query.filter(Order.billing_status.in_(billing_statuses))
    elif billing_status:
        query = query.filter(Order.billing_status == billing_status)

    if process_type_ids:
        query = query.filter(Order.process_type_id.in_(process_type_ids))
    elif process_type_id:
        query = query.filter(Order.process_type_id == process_type_id)

    if division_ids:
        query = query.filter(Order.division_id.in_(division_ids))
    elif division_id:
        query = query.filter(Order.division_id == division_id)

    if states:
        query = query.filter(Order.state.in_([s.upper() for s in states]))
    elif state:
        query = query.filter(Order.state == state.upper())
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Order.file_number.ilike(search_term),
                Order.state.ilike(search_term),
                Order.county.ilike(search_term),
                Order.product_type.ilike(search_term),
                Order.order_status.has(OrderStatusType.name.ilike(search_term))
            )
        )
    if fa_names:
        query = query.filter(
            or_(
                Order.step1_fa_name.has(FAName.name.in_(fa_names)),
                Order.step2_fa_name.has(FAName.name.in_(fa_names))
            )
        )
    elif fa_name:
        # Filter by FA name string (either step1 or step2) via the fa_names relationship
        query = query.filter(
            or_(
                Order.step1_fa_name.has(FAName.name == fa_name),
                Order.step2_fa_name.has(FAName.name == fa_name)
            )
        )
    if start_date:
        query = query.filter(Order.entry_date >= start_date)
    if end_date:
        query = query.filter(Order.entry_date <= end_date)
    
    # Get total count
    total = query.count()
    
    # Paginate - Sort by modified_at DESC (newest activity first), then by id DESC
    offset = (page - 1) * page_size
    orders = query.order_by(Order.modified_at.desc(), Order.id.desc()).offset(offset).limit(page_size).all()
    
    result = {
        "items": [serialize_simple_order(o) for o in orders],
        "total": total
    }
    
    # Cache the result
    cache.set(cache_key, result, ttl=cache.TTL_SHORT)
    
    return result


@router.get("/export")
async def export_orders(
    org_id: Optional[int] = Query(None, alias="orgId", description="Filter by organization"),
    team_id: Optional[int] = Query(None, alias="teamId", description="Filter by team"),
    order_status_id: Optional[int] = Query(None, alias="orderStatusId", description="Filter by status"),
    order_status_ids: Optional[List[int]] = Query(None, alias="orderStatusIds", description="Filter by multiple statuses"),
    step1_user_id: Optional[int] = Query(None, alias="step1UserId", description="Filter by step1 user"),
    step2_user_id: Optional[int] = Query(None, alias="step2UserId", description="Filter by step2 user"),
    my_orders: bool = Query(False, alias="myOrders", description="Filter orders where current user worked on step1 OR step2"),
    process_type_id: Optional[int] = Query(None, alias="processTypeId", description="Filter by process type"),
    process_type_ids: Optional[List[int]] = Query(None, alias="processTypeIds", description="Filter by multiple process types"),
    division_id: Optional[int] = Query(None, alias="divisionId", description="Filter by division"),
    division_ids: Optional[List[int]] = Query(None, alias="divisionIds", description="Filter by multiple divisions"),
    billing_status: Optional[str] = Query(None, alias="billingStatus", description="Filter by billing status"),
    billing_statuses: Optional[List[str]] = Query(None, alias="billingStatuses", description="Filter by multiple billing statuses"),
    state: Optional[str] = Query(None, description="Filter by state"),
    states: Optional[List[str]] = Query(None, description="Filter by multiple states"),
    search: Optional[str] = Query(None, alias="search", description="Search by file number, state, county, status, or product"),
    fa_name: Optional[str] = Query(None, alias="faName", description="Filter by FA name (step1 or step2)"),
    fa_names: Optional[List[str]] = Query(None, alias="faNames", description="Filter by multiple FA names (step1 or step2)"),
    start_date: Optional[date] = Query(None, alias="startDate", description="Filter by entry date start"),
    end_date: Optional[date] = Query(None, alias="endDate", description="Filter by entry date end"),
    include_deleted: bool = Query(False, alias="includeDeleted", description="Include soft-deleted orders"),
    max_records: int = Query(100000, ge=1, le=500000, alias="maxRecords", description="Maximum records to export"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export orders with full details for Excel export.
    Returns all matching orders with complete information (including step details, FA names, etc.)
    in a single API call. Use the same filters as list_orders.
    """
    from sqlalchemy import or_
    
    # Build cache key based on filters
    cache_key = cache._build_key(
        cache.PREFIX_ORDERS,
        "export",
        f"role:{current_user.user_role}",
        f"user:{current_user.id}",
        f"org:{org_id}" if org_id else None,
        f"team:{team_id}" if team_id else None,
        f"status:{order_status_id}" if order_status_id else None,
        f"statuses:{','.join(map(str, order_status_ids))}" if order_status_ids else None,
        f"step1:{step1_user_id}" if step1_user_id else None,
        f"step2:{step2_user_id}" if step2_user_id else None,
        f"my:{my_orders}" if my_orders else None,
        f"proc:{process_type_id}" if process_type_id else None,
        f"procs:{','.join(map(str, process_type_ids))}" if process_type_ids else None,
        f"div:{division_id}" if division_id else None,
        f"divs:{','.join(map(str, division_ids))}" if division_ids else None,
        f"bill:{billing_status}" if billing_status else None,
        f"bills:{','.join(billing_statuses)}" if billing_statuses else None,
        f"state:{state}" if state else None,
        f"states:{','.join(states)}" if states else None,
        f"search:{search}" if search else None,
        f"fa:{fa_name}" if fa_name else None,
        f"fas:{','.join(fa_names)}" if fa_names else None,
        f"start:{start_date}" if start_date else None,
        f"end:{end_date}" if end_date else None,
        f"del:{include_deleted}" if include_deleted else None,
        f"max:{max_records}"
    )
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Build query with all necessary joins for full details
    query = db.query(Order).options(
        joinedload(Order.transaction_type),
        joinedload(Order.process_type),
        joinedload(Order.order_status),
        joinedload(Order.division),
        joinedload(Order.property_type),
        joinedload(Order.step1_user),
        joinedload(Order.step2_user),
        joinedload(Order.step1_fa_name),
        joinedload(Order.step2_fa_name),
        joinedload(Order.team)
    )
    
    # Exclude soft-deleted by default
    if not include_deleted:
        query = query.filter(Order.deleted_at == None)
    
    # Apply role-based filtering
    if current_user.user_role.lower() == ROLE_SUPERADMIN:
        if org_id:
            query = query.filter(Order.org_id == org_id)
    elif current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(Order.org_id == current_user.org_id)
    elif current_user.user_role.lower() == ROLE_TEAM_LEAD:
        accessible_teams = get_user_teams(current_user, db)
        if not accessible_teams:
            return {"items": [], "total": 0}
        query = query.filter(Order.team_id.in_(accessible_teams))
    else:  # Examiner
        accessible_teams = get_user_teams(current_user, db)
        if not accessible_teams:
            return {"items": [], "total": 0}
        query = query.filter(Order.team_id.in_(accessible_teams))
    
    # Apply additional filters
    if team_id:
        query = query.filter(Order.team_id == team_id)
    if order_status_ids:
        query = query.filter(Order.order_status_id.in_(order_status_ids))
    elif order_status_id:
        query = query.filter(Order.order_status_id == order_status_id)
    
    # myOrders filter
    if my_orders:
        query = query.filter(
            or_(
                Order.step1_user_id == current_user.id,
                Order.step2_user_id == current_user.id
            )
        )
    else:
        if step1_user_id:
            query = query.filter(Order.step1_user_id == step1_user_id)
        if step2_user_id:
            query = query.filter(Order.step2_user_id == step2_user_id)
    
    if billing_statuses:
        query = query.filter(Order.billing_status.in_(billing_statuses))
    elif billing_status:
        query = query.filter(Order.billing_status == billing_status)

    if process_type_ids:
        query = query.filter(Order.process_type_id.in_(process_type_ids))
    elif process_type_id:
        query = query.filter(Order.process_type_id == process_type_id)

    if division_ids:
        query = query.filter(Order.division_id.in_(division_ids))
    elif division_id:
        query = query.filter(Order.division_id == division_id)

    if states:
        query = query.filter(Order.state.in_([s.upper() for s in states]))
    elif state:
        query = query.filter(Order.state == state.upper())
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Order.file_number.ilike(search_term),
                Order.state.ilike(search_term),
                Order.county.ilike(search_term),
                Order.product_type.ilike(search_term),
                Order.order_status.has(OrderStatusType.name.ilike(search_term))
            )
        )
    if fa_names:
        query = query.filter(
            or_(
                Order.step1_fa_name.has(FAName.name.in_(fa_names)),
                Order.step2_fa_name.has(FAName.name.in_(fa_names))
            )
        )
    elif fa_name:
        query = query.filter(
            or_(
                Order.step1_fa_name.has(FAName.name == fa_name),
                Order.step2_fa_name.has(FAName.name == fa_name)
            )
        )
    if start_date:
        query = query.filter(Order.entry_date >= start_date)
    if end_date:
        query = query.filter(Order.entry_date <= end_date)
    
    # Get total count
    total = query.count()
    
    # Limit results and sort
    orders = query.order_by(Order.entry_date.desc(), Order.id.desc()).limit(max_records).all()
    
    # Serialize with full details
    result = {
        "items": [serialize_order(o) for o in orders],
        "total": total,
        "exported": len(orders)
    }
    
    # Cache the result
    cache.set(cache_key, result, ttl=cache.TTL_MEDIUM)
    
    return result


@router.get("/filter-options/states")
async def get_available_states(
    org_id: Optional[int] = Query(None, alias="orgId", description="Filter by organization"),
    team_id: Optional[int] = Query(None, alias="teamId", description="Filter by team"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all unique states from orders based on user role and filters"""
    query = db.query(Order.state).distinct()
    
    # Exclude soft-deleted orders
    query = query.filter(Order.deleted_at == None)
    
    # Apply role-based filtering
    if current_user.user_role.lower() == ROLE_SUPERADMIN:
        if org_id:
            query = query.filter(Order.org_id == org_id)
    elif current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(Order.org_id == current_user.org_id)
    elif current_user.user_role in [ROLE_TEAM_LEAD, ROLE_EXAMINER]:
        user_teams = get_user_teams(current_user.id, db)
        team_ids = [ut.team_id for ut in user_teams if not ut.left_at]
        if team_ids:
            query = query.filter(Order.team_id.in_(team_ids))
        else:
            return []
    
    # Apply team filter if specified
    if team_id:
        query = query.filter(Order.team_id == team_id)
    
    states = [row[0] for row in query.order_by(Order.state).all() if row[0]]
    return states


@router.get("/filter-options/products")
async def get_available_products(
    org_id: Optional[int] = Query(None, alias="orgId", description="Filter by organization"),
    team_id: Optional[int] = Query(None, alias="teamId", description="Filter by team"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all unique product types from orders based on user role and filters"""
    query = db.query(Order.product_type).distinct()
    
    # Exclude soft-deleted orders
    query = query.filter(Order.deleted_at == None)
    
    # Apply role-based filtering
    if current_user.user_role.lower() == ROLE_SUPERADMIN:
        if org_id:
            query = query.filter(Order.org_id == org_id)
    elif current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(Order.org_id == current_user.org_id)
    elif current_user.user_role in [ROLE_TEAM_LEAD, ROLE_EXAMINER]:
        user_teams = get_user_teams(current_user.id, db)
        team_ids = [ut.team_id for ut in user_teams if not ut.left_at]
        if team_ids:
            query = query.filter(Order.team_id.in_(team_ids))
        else:
            return []
    
    # Apply team filter if specified
    if team_id:
        query = query.filter(Order.team_id == team_id)
    
    products = [row[0] for row in query.order_by(Order.product_type).all() if row[0]]
    return products


@router.get("/check-file/{file_number}")
async def check_file_number(
    file_number: str,
    team_id: int = Query(..., alias="teamId"),
    product_type: str = Query(..., alias="productType"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if a file number + product type combination exists for a specific team.
    The combination must be unique per team.
    Exception: If Step 1 is done, user can add Step 2 (and vice versa).
    """
    # Check team access (still needed to validate the team_id parameter)
    if not check_team_access(current_user, team_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access this team"
        )
    
    # Determine if this user can create duplicates for this product. The
    # frontend can then ask whether to use the existing order or create a
    # duplicate entry.
    duplicates_allowed = can_create_duplicate_for_product(current_user, product_type, db)
    matching_orders = get_matching_orders(db, file_number, product_type, team_id)
    available_step = find_available_step_candidate(matching_orders)

    if available_step:
        existing = available_step["order"]
        step1_completed = existing.step1_user_id is not None
        step2_completed = existing.step2_user_id is not None

        return {
            "exists": True,
            "fileNumber": file_number,
            "productType": product_type,
            "orderId": existing.id,
            "step1Completed": step1_completed,
            "step2Completed": step2_completed,
            "step1UserId": existing.step1_user_id,
            "step1UserName": existing.step1_user.user_name if existing.step1_user else None,
            "step2UserId": existing.step2_user_id,
            "step2UserName": existing.step2_user.user_name if existing.step2_user else None,
            "sameTeam": True,
            "teamId": existing.team_id,
            "duplicatesAllowed": duplicates_allowed,
            "existingOrderDetails": {
                "state": existing.state,
                "county": existing.county,
                "productType": existing.product_type,
                "productionType": existing.production_type,
                "transactionTypeId": existing.transaction_type_id,
                "orderStatusId": existing.order_status_id,
                "divisionId": existing.division_id,
                "propertyTypeId": existing.property_type_id,
                "entryDate": existing.entry_date.isoformat() if existing.entry_date else None
            }
        }

    existing = matching_orders[0] if matching_orders else None

    if duplicates_allowed and existing:
        return {
            "exists": True,
            "fileNumber": file_number,
            "productType": product_type,
            "orderId": existing.id,
            "step1Completed": existing.step1_user_id is not None,
            "step2Completed": existing.step2_user_id is not None,
            "step1UserId": existing.step1_user_id,
            "step1UserName": existing.step1_user.user_name if existing.step1_user else None,
            "step2UserId": existing.step2_user_id,
            "step2UserName": existing.step2_user.user_name if existing.step2_user else None,
            "sameTeam": True,
            "teamId": existing.team_id,
            "duplicatesAllowed": True,
            "existingOrderDetails": {
                "state": existing.state,
                "county": existing.county,
                "productType": existing.product_type,
                "productionType": existing.production_type,
                "transactionTypeId": existing.transaction_type_id,
                "orderStatusId": existing.order_status_id,
                "divisionId": existing.division_id,
                "propertyTypeId": existing.property_type_id,
                "entryDate": existing.entry_date.isoformat() if existing.entry_date else None
            }
        }

    if not existing:
        # File + product_type + team combination doesn't exist - new order allowed
        return {
            "exists": False,
            "fileNumber": file_number,
            "productType": product_type,
            "step1Completed": False,
            "step2Completed": False,
            "orderId": None,
            "sameTeam": True,  # Always true since we're checking within the same team
            "duplicatesAllowed": False,
        }
    
    # File + product_type + team combination exists, but no missing step can be
    # added by this request path.
    step1_completed = existing.step1_user_id is not None
    step2_completed = existing.step2_user_id is not None
    
    return {
        "exists": True,
        "fileNumber": file_number,
        "productType": product_type,
        "orderId": existing.id,
        "step1Completed": step1_completed,
        "step2Completed": step2_completed,
        "step1UserId": existing.step1_user_id,
        "step1UserName": existing.step1_user.user_name if existing.step1_user else None,
        "step2UserId": existing.step2_user_id,
        "step2UserName": existing.step2_user.user_name if existing.step2_user else None,
        "sameTeam": True,  # Always true since we're checking within the same team
        "teamId": existing.team_id,
        "duplicatesAllowed": False,
        # Include existing order details so frontend can use them if adding Step 2
        "existingOrderDetails": {
            "state": existing.state,
            "county": existing.county,
            "productType": existing.product_type,
            "productionType": existing.production_type,
            "transactionTypeId": existing.transaction_type_id,
            "orderStatusId": existing.order_status_id,
            "divisionId": existing.division_id,
            "propertyTypeId": existing.property_type_id,
            "entryDate": existing.entry_date.isoformat() if existing.entry_date else None
        }
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new order or update existing order with the other step.
    
    Logic:
    - If file_number/product/team has a compatible missing step: update that order
    - If the combination exists without a mergeable missing step: create a duplicate only when allowed
    - Otherwise create a new order
    """
    logger.info(f"POST /orders - file_number={order_data.file_number}, user={current_user.id}")
    
    # Import Organization model
    from app.models.organization import Organization
    from app.models.reference import ProcessType
    
    # Check organization access
    if not check_org_access(current_user, order_data.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order in this organization"
        )
    
    # Check if organization is active
    organization = db.query(Organization).filter(Organization.id == order_data.org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    if not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create order for inactive organization"
        )
    
    # Check team access
    if not check_team_access(current_user, order_data.team_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order for this team"
        )
    
    # Check if team is active
    team = db.query(Team).filter(Team.id == order_data.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    if not team.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create order for inactive team"
        )
    
    # Get the process type name to determine step logic
    process_type = db.query(ProcessType).filter(ProcessType.id == order_data.process_type_id).first()
    if not process_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process type not found"
        )
    
    # For selected product types duplicates are allowed per team. Unless the user
    # explicitly chose duplicate entry, complete a compatible partial order first.
    product_allows_duplicates = can_create_duplicate_for_product(current_user, order_data.product_type, db)
    force_duplicate = bool(order_data.force_duplicate)
    adding_step1 = order_data.step1_user_id is not None
    adding_step2 = order_data.step2_user_id is not None
    matching_orders = get_matching_orders(
        db,
        order_data.file_number,
        order_data.product_type,
        order_data.team_id,
    )
    merge_candidate = find_merge_candidate(
        matching_orders,
        adding_step1,
        adding_step2,
        process_type.name,
    )

    if force_duplicate and matching_orders and not product_allows_duplicates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Duplicate entry is not allowed for file number '{order_data.file_number}' "
                f"with product type '{order_data.product_type}' in this team"
            ),
        )

    if merge_candidate and not force_duplicate:
        allow_non_team_member = current_user.user_role.lower() in [ROLE_SUPERADMIN, ROLE_ADMIN]

        if adding_step1 and order_data.step1_user_id:
            validate_user_for_step_assignment(
                db,
                order_data.step1_user_id,
                order_data.team_id,
                "Step 1",
                allow_non_team_member=allow_non_team_member,
            )
        if adding_step2 and order_data.step2_user_id:
            validate_user_for_step_assignment(
                db,
                order_data.step2_user_id,
                order_data.team_id,
                "Step 2",
                allow_non_team_member=allow_non_team_member,
            )

        apply_step_merge(
            db,
            merge_candidate,
            current_user.id,
            step1_user_id=order_data.step1_user_id if adding_step1 else None,
            step1_fa_name_id=order_data.step1_fa_name_id if adding_step1 else None,
            step2_user_id=order_data.step2_user_id if adding_step2 else None,
            step2_fa_name_id=order_data.step2_fa_name_id if adding_step2 else None,
        )
        db.commit()

        # Invalidate dashboard caches for this organization
        cache.invalidate_dashboard_cache(org_id=order_data.org_id)
        cache.invalidate_order_cache()
        cache.invalidate_productivity_cache()
        cache.invalidate_billing_cache()
        
        # Reload with relationships
        order = db.query(Order).options(
            joinedload(Order.transaction_type),
            joinedload(Order.process_type),
            joinedload(Order.order_status),
            joinedload(Order.division),
            joinedload(Order.step1_user),
            joinedload(Order.step2_user),
            joinedload(Order.step1_fa_name),
            joinedload(Order.step2_fa_name)
        ).filter(Order.id == merge_candidate.id).first()

        return serialize_order(order)

    if matching_orders and not product_allows_duplicates:
        existing = matching_orders[0]
        if process_type.name == "Single Seat":
            detail = (
                f"File number '{order_data.file_number}' with product type "
                f"'{order_data.product_type}' already exists. Cannot create a Single Seat order."
            )
        elif adding_step1 and existing.step1_user_id is not None:
            detail = (
                f"Step 1 for file '{order_data.file_number}' is already completed by "
                f"{existing.step1_user.user_name if existing.step1_user else 'another user'}"
            )
        elif adding_step2 and existing.step2_user_id is not None:
            detail = (
                f"Step 2 for file '{order_data.file_number}' is already completed by "
                f"{existing.step2_user.user_name if existing.step2_user else 'another user'}"
            )
        else:
            detail = (
                f"File number '{order_data.file_number}' with product type "
                f"'{order_data.product_type}' already exists in this team"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    # No mergeable existing order - create a new order.
    allow_non_team_member = current_user.user_role.lower() in [ROLE_SUPERADMIN, ROLE_ADMIN]

    # Validate step1 user assignment (if provided)
    if order_data.step1_user_id:
        validate_user_for_step_assignment(
            db,
            order_data.step1_user_id,
            order_data.team_id,
            "Step 1",
            allow_non_team_member=allow_non_team_member,
        )
    
    # Validate step2 user assignment (if provided)
    if order_data.step2_user_id:
        validate_user_for_step_assignment(
            db,
            order_data.step2_user_id,
            order_data.team_id,
            "Step 2",
            allow_non_team_member=allow_non_team_member,
        )
    
    # Create order
    order = Order(
        file_number=order_data.file_number,
        entry_date=order_data.entry_date,
        transaction_type_id=order_data.transaction_type_id,
        process_type_id=order_data.process_type_id,
        order_status_id=order_data.order_status_id,
        division_id=order_data.division_id,
        state=order_data.state.upper(),
        county=order_data.county,
        product_type=order_data.product_type,
        production_type=order_data.production_type,  # Add production_type field
        property_type_id=order_data.property_type_id,
        team_id=order_data.team_id,
        org_id=order_data.org_id,
        step1_user_id=order_data.step1_user_id,
        step1_fa_name_id=order_data.step1_fa_name_id,
        step2_user_id=order_data.step2_user_id,
        step2_fa_name_id=order_data.step2_fa_name_id,
        created_by=current_user.id
    )
    
    db.add(order)
    db.flush()
    
    # Log creation
    log_order_change(db, order.id, current_user.id, "order", None, order_data.file_number, "create")
    
    db.commit()
    
    # Invalidate dashboard caches for this organization
    cache.invalidate_dashboard_cache(org_id=order_data.org_id)
    cache.invalidate_order_cache()
    cache.invalidate_productivity_cache()
    cache.invalidate_billing_cache()
    
    # Reload with relationships
    order = db.query(Order).options(
        joinedload(Order.transaction_type),
        joinedload(Order.process_type),
        joinedload(Order.order_status),
        joinedload(Order.division),
        joinedload(Order.step1_user),
        joinedload(Order.step2_user),
        joinedload(Order.step1_fa_name),
        joinedload(Order.step2_fa_name)
    ).filter(Order.id == order.id).first()
    
    logger.info(f"Order created: id={order.id}, file_number={order.file_number}")
    return serialize_order(order)


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get order by ID with full details"""
    try:
        logger.info(f"GET /orders/{order_id} - User: {current_user.id}")
        
        order = db.query(Order).options(
            joinedload(Order.transaction_type),
            joinedload(Order.process_type),
            joinedload(Order.order_status),
            joinedload(Order.division),
            joinedload(Order.property_type),
            joinedload(Order.step1_user),
            joinedload(Order.step2_user),
            joinedload(Order.step1_fa_name),
            joinedload(Order.step2_fa_name)
        ).filter(Order.id == order_id).first()
        
        if not order:
            logger.warning(f"Order {order_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        logger.info(f"Order {order_id}: file={order.file_number}, step1_user={order.step1_user_id}, step2_user={order.step2_user_id}")
        
        # Check access - team members can view all orders in their team
        if current_user.user_role.lower() == ROLE_SUPERADMIN:
            pass  # Full access
        elif current_user.user_role.lower() == ROLE_ADMIN:
            if order.org_id != current_user.org_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
        elif current_user.user_role.lower() == ROLE_TEAM_LEAD:
            if not check_team_access(current_user, order.team_id, db):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
        else:  # Employee
            # Employees can view any order in their team
            if not check_team_access(current_user, order.team_id, db):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
        
        # Add edit permissions info to the response
        logger.info(f"Serializing order {order_id}")
        order_dict = serialize_order(order)
        order_dict["editPermissions"] = get_edit_permissions(order, current_user)
        
        logger.info(f"GET /orders/{order_id} successful")
        return order_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in GET /orders/{order_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching order: {str(e)}"
        )


def get_edit_permissions(order: Order, user: User) -> dict:
    """
    Determine what a user can edit on an order.
    
    Rules:
    - Billing done: No one can edit (hard lock for all roles)
    - Superadmin/Admin/Team Lead: Can edit everything (while billing is pending)
    - Employee:
      - Single Seat orders: Only the assigned user can edit (no one else)
      - Step1/Step2 orders: Steps are INDEPENDENT
        - Can edit Step 1 if: they did it OR it's not done yet
        - Can edit Step 2 if: they did it OR it's not done yet
        - Cannot edit someone else's completed step
    """
    # Hard lock: once billing is done, no one can edit
    if order.billing_status == 'done':
        return {
            "canEdit": False,
            "canEditStep1": False,
            "canEditStep2": False,
            "canEditOrderDetails": False,
            "canEditOrderStatus": False,
            "reason": "Order billing is completed — editing is locked"
        }
    
    process_type_name = order.process_type.name if order.process_type else None
    
    # Admin/Team Lead have full access
    if user.user_role in [ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD]:
        return {
            "canEdit": True,
            "canEditStep1": True,
            "canEditStep2": True,
            "canEditOrderDetails": True,
            "canEditOrderStatus": True,
            "reason": "Full access"
        }
    
    # Employee permissions
    is_step1_user = order.step1_user_id == user.id
    is_step2_user = order.step2_user_id == user.id
    step1_done = order.step1_user_id is not None
    step2_done = order.step2_user_id is not None
    
    # Single Seat - permission depends on whether one or two examiners worked on it
    if process_type_name == "Single Seat":
        sole_examiner = (
            order.step1_user_id is not None and
            order.step1_user_id == order.step2_user_id
        )
        if sole_examiner and is_step1_user:
            # This examiner is the only one who worked on it — full edit access
            return {
                "canEdit": True,
                "canEditStep1": True,
                "canEditStep2": True,
                "canEditOrderDetails": True,
                "canEditOrderStatus": True,
                "reason": "You are the sole examiner on this order"
            }
        elif not sole_examiner and (is_step1_user or is_step2_user):
            # Two different examiners worked on this order — FA name only for their step
            # But they can still update the order status (e.g., mark as completed)
            return {
                "canEdit": True,
                "canEditStep1": is_step1_user,
                "canEditStep2": is_step2_user,
                "canEditOrderDetails": False,
                "canEditOrderStatus": True,
                "reason": "You can update your FA name and order status"
            }
        else:
            return {
                "canEdit": False,
                "canEditStep1": False,
                "canEditStep2": False,
                "canEditOrderDetails": False,
                "canEditOrderStatus": False,
                "reason": "Single Seat order completed by another examiner"
            }
    
    # Step1/Step2 process types - steps are independent.
    # A different examiner may claim the missing complementary step from edit
    # mode, but the original step owner is not forced into the other step.
    can_claim_step1 = (not step1_done) and step2_done and (not is_step2_user)
    can_claim_step2 = (not step2_done) and step1_done and (not is_step1_user)
    can_edit_step1 = is_step1_user or can_claim_step1
    can_edit_step2 = is_step2_user or can_claim_step2

    can_edit = can_edit_step1 or can_edit_step2

    # Examiners assigned to either step can update the order status
    # (e.g., Step 2 examiner marking the order as completed)
    can_edit_order_status = is_step1_user or is_step2_user

    # If the examiner can update order status, they should be able to edit the order
    can_edit = can_edit or can_edit_order_status

    reasons = []
    if can_edit_step1:
        if is_step1_user:
            reasons.append("You completed Step 1")
        elif not step1_done:
            reasons.append("Step 1 is available")
    if can_edit_step2:
        if is_step2_user:
            reasons.append("You completed Step 2")
        elif not step2_done:
            reasons.append("Step 2 is available")
    if can_edit_order_status:
        reasons.append("You can update order status")

    if not can_edit:
        if step1_done and step2_done:
            reason = "Both steps were completed by other examiners"
        elif step1_done:
            reason = "Step 1 was completed by another examiner"
        elif step2_done:
            reason = "Step 2 was completed by another examiner"
        else:
            reason = "No edit access"
    else:
        reason = "; ".join(reasons) if reasons else "No edit access"

    return {
        "canEdit": can_edit,
        "canEditStep1": can_edit_step1,
        "canEditStep2": can_edit_step2,
        "canEditOrderDetails": False,  # Employees cannot edit order details
        "canEditOrderStatus": can_edit_order_status,
        "reason": reason
    }


@router.put("/{order_id}")
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update order with role-based edit restrictions"""
    order = db.query(Order).options(
        joinedload(Order.transaction_type),
        joinedload(Order.process_type),
        joinedload(Order.order_status),
        joinedload(Order.division),
        joinedload(Order.step1_user),
        joinedload(Order.step2_user),
        joinedload(Order.step1_fa_name),
        joinedload(Order.step2_fa_name)
    ).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check soft delete
    if order.deleted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update deleted order")

    user_role = current_user.user_role.lower()

    # Enforce the same order access boundaries used by the read endpoints.
    if user_role == ROLE_SUPERADMIN:
        pass
    elif user_role == ROLE_ADMIN:
        if order.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    elif user_role in [ROLE_TEAM_LEAD, ROLE_EXAMINER]:
        if not check_team_access(current_user, order.team_id, db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    
    # Hard lock: billing-done orders cannot be edited by anyone
    if order.billing_status == 'done':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order billing is completed — editing is locked"
        )
    
    # Get edit permissions for this user
    edit_perms = get_edit_permissions(order, current_user)
    
    if not edit_perms["canEdit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Cannot edit this order: {edit_perms['reason']}"
        )
    
    update_data = order_data.model_dump(exclude_unset=True)

    # Entry date can be edited only by admin/superadmin/team lead.
    if 'entry_date' in update_data:
        if user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD]:
            if update_data['entry_date'] != order.entry_date:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admin, superadmin, and team lead can edit entry date"
                )
            del update_data['entry_date']
    
    # Define field categories
    order_detail_fields = ['file_number', 'entry_date', 'transaction_type_id', 'process_type_id', 
                          'division_id', 'state', 'county', 
                          'product_type', 'production_type', 'team_id', 'billing_status']
    order_status_fields = ['order_status_id']
    step1_fields = ['step1_user_id', 'step1_fa_name_id']
    step2_fields = ['step2_user_id', 'step2_fa_name_id']
    
    # Validate field access for examiners
    # We need to check if values are actually changing, not just if they're present
    if current_user.user_role.lower() == ROLE_EXAMINER:
        fields_to_remove = []  # Track fields that aren't actually changing
        
        for field, new_value in update_data.items():
            old_value = getattr(order, field)
            value_is_changing = old_value != new_value
            
            # Check order detail fields - only block if value is actually changing
            if field in order_detail_fields and not edit_perms["canEditOrderDetails"]:
                if value_is_changing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Employees cannot modify order details ({field})"
                    )
                else:
                    # Value isn't changing, remove from update to skip unnecessary processing
                    fields_to_remove.append(field)
            
            # Check order status field separately — examiners assigned to either step can update it
            if field in order_status_fields and not edit_perms.get("canEditOrderStatus", False):
                if value_is_changing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Cannot modify order status — you are not assigned to this order"
                    )
                else:
                    fields_to_remove.append(field)
            
            # Check step1 fields
            if field in step1_fields and not edit_perms["canEditStep1"]:
                if value_is_changing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Cannot modify Step 1 - it was completed by another examiner"
                    )
                else:
                    fields_to_remove.append(field)
            
            # Check step2 fields
            if field in step2_fields and not edit_perms["canEditStep2"]:
                if value_is_changing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Cannot modify Step 2 - it was completed by another examiner"
                    )
                else:
                    fields_to_remove.append(field)
        
        # Remove unchanged fields that examiner shouldn't modify
        for field in fields_to_remove:
            del update_data[field]
    
    # Determine the team_id to use for validation (could be updated or existing)
    team_id_for_validation = update_data.get('team_id', order.team_id)
    allow_non_team_member = current_user.user_role.lower() in [ROLE_SUPERADMIN, ROLE_ADMIN]

    # Validate step1 user assignment (if being updated)
    if 'step1_user_id' in update_data and update_data['step1_user_id'] is not None:
        validate_user_for_step_assignment(
            db,
            update_data['step1_user_id'],
            team_id_for_validation,
            "Step 1",
            allow_non_team_member=allow_non_team_member,
        )

    # Validate step2 user assignment (if being updated)
    if 'step2_user_id' in update_data and update_data['step2_user_id'] is not None:
        validate_user_for_step_assignment(
            db,
            update_data['step2_user_id'],
            team_id_for_validation,
            "Step 2",
            allow_non_team_member=allow_non_team_member,
        )

    # Enforce duplicate behavior against other rows with the same file/product/team.
    # If a compatible partial order exists, merge into it before allowing duplicate mode.
    prospective_file_number = update_data.get('file_number', order.file_number)
    prospective_product_type = update_data.get('product_type', order.product_type)
    prospective_team_id = update_data.get('team_id', order.team_id)

    requested_process_type_name = order.process_type.name if order.process_type else None
    if 'process_type_id' in update_data:
        from app.models.reference import ProcessType
        requested_process_type = db.query(ProcessType).filter(
            ProcessType.id == update_data['process_type_id']
        ).first()
        if not requested_process_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process type not found"
            )
        requested_process_type_name = requested_process_type.name

    prospective_step1_user_id = update_data.get('step1_user_id', order.step1_user_id)
    prospective_step2_user_id = update_data.get('step2_user_id', order.step2_user_id)
    adding_step1_for_merge = (
        prospective_step1_user_id is not None and
        prospective_step2_user_id is None
    )
    adding_step2_for_merge = (
        prospective_step2_user_id is not None and
        prospective_step1_user_id is None
    )

    matching_orders = get_matching_orders(
        db,
        prospective_file_number,
        prospective_product_type,
        prospective_team_id,
        exclude_order_id=order.id,
    )
    merge_candidate = find_merge_candidate(
        matching_orders,
        adding_step1_for_merge,
        adding_step2_for_merge,
        requested_process_type_name,
    )

    if merge_candidate:
        apply_step_merge(
            db,
            merge_candidate,
            current_user.id,
            step1_user_id=prospective_step1_user_id if adding_step1_for_merge else None,
            step1_fa_name_id=update_data.get('step1_fa_name_id', order.step1_fa_name_id) if adding_step1_for_merge else None,
            step2_user_id=prospective_step2_user_id if adding_step2_for_merge else None,
            step2_fa_name_id=update_data.get('step2_fa_name_id', order.step2_fa_name_id) if adding_step2_for_merge else None,
        )

        order.deleted_at = datetime.utcnow()
        order.deleted_by = current_user.id
        order.modified_by = current_user.id
        log_order_change(
            db, order.id, current_user.id, "merged_into_order_id",
            None, str(merge_candidate.id), "merge"
        )
        log_order_change(
            db, order.id, current_user.id, "deleted_at",
            None, str(order.deleted_at), "delete"
        )

        db.commit()

        cache.invalidate_dashboard_cache(org_id=merge_candidate.org_id)
        cache.invalidate_order_cache()
        cache.invalidate_productivity_cache()
        cache.invalidate_billing_cache()

        merged_order = db.query(Order).options(
            joinedload(Order.transaction_type),
            joinedload(Order.process_type),
            joinedload(Order.order_status),
            joinedload(Order.division),
            joinedload(Order.property_type),
            joinedload(Order.step1_user),
            joinedload(Order.step2_user),
            joinedload(Order.step1_fa_name),
            joinedload(Order.step2_fa_name)
        ).filter(Order.id == merge_candidate.id).first()

        order_dict = serialize_order(merged_order)
        order_dict["editPermissions"] = get_edit_permissions(merged_order, current_user)
        return order_dict

    if matching_orders and not can_create_duplicate_for_product(current_user, prospective_product_type, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File number '{prospective_file_number}' with product type "
                f"'{prospective_product_type}' already exists in this team"
            ),
        )
    
    # Log changes and update
    for field, new_value in update_data.items():
        old_value = getattr(order, field)
        if old_value != new_value:
            log_order_change(
                db, order.id, current_user.id, field,
                str(old_value) if old_value else None,
                str(new_value) if new_value else None,
                "update"
            )
            setattr(order, field, new_value)
    
    order.modified_by = current_user.id
    db.commit()
    db.refresh(order)
    
    # Invalidate dashboard caches for this organization
    cache.invalidate_dashboard_cache(org_id=order.org_id)
    cache.invalidate_order_cache()
    cache.invalidate_productivity_cache()
    cache.invalidate_billing_cache()
    
    # Return with updated edit permissions
    order_dict = serialize_order(order)
    order_dict["editPermissions"] = get_edit_permissions(order, current_user)
    
    return order_dict


@router.post("/bulk/billing-status")
async def bulk_update_billing_status(
    data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Bulk update billing status for multiple orders (Admin or Superadmin only)"""
    order_ids = data.get("orderIds", [])
    billing_status = data.get("billingStatus")
    
    if not order_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No order IDs provided"
        )
    
    if billing_status not in ["pending", "done"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid billing status. Must be 'pending' or 'done'"
        )
    
    # Get orders
    query = db.query(Order).filter(Order.id.in_(order_ids), Order.deleted_at == None)
    
    # Admin can only update orders in their organization
    if current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(Order.org_id == current_user.org_id)
    
    orders = query.all()
    
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found with the provided IDs"
        )
    
    updated_count = 0
    for order in orders:
        if order.billing_status != billing_status:
            log_order_change(
                db, order.id, current_user.id, "billing_status",
                order.billing_status, billing_status, "update"
            )
            order.billing_status = billing_status
            order.modified_by = current_user.id
            updated_count += 1
    
    db.commit()
    
    # Invalidate dashboard caches for affected organizations
    if updated_count > 0:
        cache.invalidate_dashboard_cache()  # Invalidate all dashboard caches since orders could be from different orgs
        cache.invalidate_order_cache()
        cache.invalidate_billing_cache()
    
    return {"message": f"Updated billing status for {updated_count} orders"}


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Soft delete an order (Admin or Superadmin only)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.deleted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already deleted")
    
    # Cannot delete orders after billing is done
    if order.billing_status == 'done':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete order after billing is done"
        )
    
    # Check organization access for admin
    if current_user.user_role.lower() == ROLE_ADMIN:
        if order.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    
    # Soft delete
    order.deleted_at = datetime.utcnow()
    order.deleted_by = current_user.id
    order.modified_by = current_user.id
    
    log_order_change(db, order.id, current_user.id, "deleted_at", None, str(order.deleted_at), "delete")
    
    db.commit()
    
    # Invalidate dashboard caches for this organization
    cache.invalidate_dashboard_cache(org_id=order.org_id)
    cache.invalidate_order_cache()
    cache.invalidate_productivity_cache()
    cache.invalidate_billing_cache()


@router.post("/{order_id}/restore")
async def restore_order(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted order (Admin or Superadmin only)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if not order.deleted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not deleted")
    
    # Check organization access for admin
    if current_user.user_role.lower() == ROLE_ADMIN:
        if order.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    
    # Restore
    old_deleted_at = str(order.deleted_at)
    order.deleted_at = None
    order.deleted_by = None
    order.modified_by = current_user.id
    
    log_order_change(db, order.id, current_user.id, "deleted_at", old_deleted_at, None, "restore")
    
    db.commit()
    
    # Invalidate dashboard caches for this organization
    cache.invalidate_dashboard_cache(org_id=order.org_id)
    cache.invalidate_order_cache()
    cache.invalidate_productivity_cache()
    cache.invalidate_billing_cache()
    
    # Reload with relationships
    order = db.query(Order).options(
        joinedload(Order.transaction_type),
        joinedload(Order.process_type),
        joinedload(Order.order_status),
        joinedload(Order.division),
        joinedload(Order.step1_user),
        joinedload(Order.step2_user)
    ).filter(Order.id == order_id).first()
    
    return serialize_order(order)


@router.get("/{order_id}/history")
async def get_order_history(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit history for an order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check access
    if current_user.user_role.lower() == ROLE_ADMIN:
        if order.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    elif current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not check_team_access(current_user, order.team_id, db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    elif current_user.user_role.lower() == ROLE_EXAMINER:
        if order.step1_user_id != current_user.id and order.step2_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")
    
    history = db.query(OrderHistory).options(
        joinedload(OrderHistory.changed_by_user)
    ).filter(
        OrderHistory.order_id == order_id
    ).order_by(OrderHistory.changed_at.desc()).all()
    
    return [serialize_order_history(h) for h in history]
