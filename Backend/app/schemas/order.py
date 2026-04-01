"""
Order Schemas
Pydantic schemas for order management with step-based workflow
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from datetime import date, datetime


# ============ Order Schemas ============
class OrderBase(BaseModel):
    file_number: str = Field(..., max_length=100, alias="fileNumber")
    entry_date: date = Field(..., alias="entryDate")
    transaction_type_id: int = Field(..., alias="transactionTypeId")
    process_type_id: int = Field(..., alias="processTypeId")
    order_status_id: int = Field(..., alias="orderStatusId")
    division_id: int = Field(..., alias="divisionId")
    property_type_id: int = Field(..., alias="propertyTypeId")
    state: str = Field(..., max_length=50)
    county: str = Field(..., max_length=100)
    product_type: str = Field(..., max_length=100, alias="productType")
    production_type: str = Field(default='regular', max_length=20, alias="productionType")
    team_id: int = Field(..., alias="teamId")
    org_id: int = Field(..., alias="orgId")


class OrderCreate(OrderBase):
    # Step 1 (optional on create)
    step1_user_id: Optional[int] = Field(None, alias="step1UserId")
    step1_fa_name_id: Optional[int] = Field(None, alias="step1FaNameId")
    
    # Step 2 (optional on create)
    step2_user_id: Optional[int] = Field(None, alias="step2UserId")
    step2_fa_name_id: Optional[int] = Field(None, alias="step2FaNameId")


class OrderUpdate(BaseModel):
    file_number: Optional[str] = Field(None, max_length=100, alias="fileNumber")
    entry_date: Optional[date] = Field(None, alias="entryDate")
    transaction_type_id: Optional[int] = Field(None, alias="transactionTypeId")
    process_type_id: Optional[int] = Field(None, alias="processTypeId")
    order_status_id: Optional[int] = Field(None, alias="orderStatusId")
    division_id: Optional[int] = Field(None, alias="divisionId")
    property_type_id: Optional[int] = Field(None, alias="propertyTypeId")
    state: Optional[str] = Field(None, max_length=50)
    county: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100, alias="productType")
    production_type: Optional[str] = Field(None, max_length=20, alias="productionType")
    team_id: Optional[int] = Field(None, alias="teamId")
    
    # Step 1 updates
    step1_user_id: Optional[int] = Field(None, alias="step1UserId")
    step1_fa_name_id: Optional[int] = Field(None, alias="step1FaNameId")
    
    # Step 2 updates
    step2_user_id: Optional[int] = Field(None, alias="step2UserId")
    step2_fa_name_id: Optional[int] = Field(None, alias="step2FaNameId")
    
    billing_status: Optional[str] = Field(None, alias="billingStatus")

    class Config:
        populate_by_name = True


class StepInfo(BaseModel):
    """Step information embedded in order response"""
    user_id: Optional[int] = Field(None, alias="userId")
    user_name: Optional[str] = Field(None, alias="userName")
    employee_id: Optional[str] = Field(None, alias="employeeId")
    fa_name: Optional[str] = Field(None, alias="faName")
    fa_name_id: Optional[int] = Field(None, alias="faNameId")

    class Config:
        populate_by_name = True


class ReferenceTypeInfo(BaseModel):
    """Embedded reference type info"""
    id: int
    name: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    file_number: str = Field(..., alias="fileNumber")
    entry_date: date = Field(..., alias="entryDate")
    
    # Reference data (expanded)
    transaction_type_id: int = Field(..., alias="transactionTypeId")
    transaction_type: Optional[ReferenceTypeInfo] = Field(None, alias="transactionType")
    process_type_id: int = Field(..., alias="processTypeId")
    process_type: Optional[ReferenceTypeInfo] = Field(None, alias="processType")
    order_status_id: int = Field(..., alias="orderStatusId")
    order_status: Optional[ReferenceTypeInfo] = Field(None, alias="orderStatus")
    division_id: int = Field(..., alias="divisionId")
    division: Optional[ReferenceTypeInfo] = None
    property_type_id: Optional[int] = Field(None, alias="propertyTypeId")
    property_type: Optional[ReferenceTypeInfo] = Field(None, alias="propertyType")
    
    # Location
    state: str
    county: str
    
    # Product and assignment
    product_type: str = Field(..., alias="productType")
    production_type: str = Field(..., alias="productionType")
    team_id: int = Field(..., alias="teamId")
    org_id: int = Field(..., alias="orgId")
    
    # Steps
    step1: Optional[StepInfo] = None
    step2: Optional[StepInfo] = None
    
    # Billing
    billing_status: str = Field(..., alias="billingStatus")
    
    # Audit
    created_by: int = Field(..., alias="createdBy")
    modified_by: Optional[int] = Field(None, alias="modifiedBy")
    created_at: datetime = Field(..., alias="createdAt")
    modified_at: datetime = Field(..., alias="modifiedAt")
    deleted_at: Optional[datetime] = Field(None, alias="deletedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class OrderSimpleResponse(BaseModel):
    """Simplified order response for lists"""
    id: int
    file_number: str = Field(..., alias="fileNumber")
    entry_date: date = Field(..., alias="entryDate")
    state: str
    county: str
    product_type: str = Field(..., alias="productType")
    production_type: str = Field(..., alias="productionType")
    transaction_type_name: Optional[str] = Field(None, alias="transactionTypeName")
    process_type_name: Optional[str] = Field(None, alias="processTypeName")
    order_status_name: Optional[str] = Field(None, alias="orderStatusName")
    division_name: Optional[str] = Field(None, alias="divisionName")
    property_type_name: Optional[str] = Field(None, alias="propertyTypeName")
    team_id: int = Field(..., alias="teamId")
    billing_status: str = Field(..., alias="billingStatus")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class OrderListResponse(BaseModel):
    items: List[OrderSimpleResponse]
    total: int


class OrderFilterParams(BaseModel):
    """Filter parameters for order queries"""
    org_id: Optional[int] = Field(None, alias="orgId")
    team_id: Optional[int] = Field(None, alias="teamId")
    order_status_id: Optional[int] = Field(None, alias="orderStatusId")
    step1_user_id: Optional[int] = Field(None, alias="step1UserId")
    step2_user_id: Optional[int] = Field(None, alias="step2UserId")
    billing_status: Optional[str] = Field(None, alias="billingStatus")
    state: Optional[str] = None
    start_date: Optional[date] = Field(None, alias="startDate")
    end_date: Optional[date] = Field(None, alias="endDate")
    include_deleted: bool = Field(False, alias="includeDeleted")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100, alias="pageSize")

    class Config:
        populate_by_name = True
