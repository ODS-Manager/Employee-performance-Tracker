"""
Billing Schemas
Pydantic models for billing report requests and responses
Now billing is done organization-wide by product type (not by team)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date


class BillingDetailResponse(BaseModel):
    """Billing detail for a product type (team + product type + division combination)"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)
    
    id: int
    state: Optional[str] = None  # NULL for org-wide reports
    team_name: str = Field(alias="teamName")  # Full team name (e.g., "National Streamline", "Florida")
    product_type: str = Field(alias="productType")  # Format: "WA Full Search" (with team code prefix)
    product_name: str = Field(alias="productName")  # Product name only (e.g., "Full Search", "Amend Title")
    division_id: int = Field(alias="divisionId")  # Direct=1, Agency=2 (reference to divisions table)
    division_name: Optional[str] = Field(None, alias="divisionName")  # "Direct" or "Agency"
    single_seat_count: int = Field(alias="singleSeatCount")
    only_step1_count: int = Field(alias="onlyStep1Count")
    only_step2_count: int = Field(alias="onlyStep2Count")
    total_count: int = Field(alias="totalCount")


class BillingReportResponse(BaseModel):
    """Billing report response with details - organization-wide, no team filtering"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)
    
    id: int
    org_id: int = Field(alias="orgId")
    team_id: Optional[int] = Field(None, alias="teamId")  # Always null for org-wide reports
    team_name: Optional[str] = Field("All Teams", alias="teamName")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    status: str
    created_by: int = Field(alias="createdBy")
    created_by_name: Optional[str] = Field(None, alias="createdByName")
    finalized_by: Optional[int] = Field(None, alias="finalizedBy")
    finalized_by_name: Optional[str] = Field(None, alias="finalizedByName")
    finalized_at: Optional[datetime] = Field(None, alias="finalizedAt")
    created_at: datetime = Field(alias="createdAt")
    modified_at: datetime = Field(alias="modifiedAt")
    details: List[BillingDetailResponse] = []
    
    # Summary totals
    total_files: int = Field(0, alias="totalFiles")


class BillingReportListResponse(BaseModel):
    """List of billing reports"""
    items: List[BillingReportResponse]
    total: int


class BillingReportCreate(BaseModel):
    """Create a new billing report (admin/superadmin only) - always organization-wide"""
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    org_id: Optional[int] = Field(default=None, alias="orgId")  # Required for superadmin


class BillingReportFinalize(BaseModel):
    """Finalize a billing report - marks all orders as done"""
    pass  # No additional fields needed


class BillingPreviewRequest(BaseModel):
    """Request to preview billing data before generating report"""
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    org_id: Optional[int] = Field(default=None, alias="orgId")  # Required for superadmin


class BillingPreviewDetail(BaseModel):
    """Preview detail - grouped by product type and division with team prefix"""
    team_name: str = Field(alias="teamName")  # Full team name (e.g., "National Streamline", "Florida")
    product_type: str = Field(alias="productType")  # Format: "WA Full Search" (with team code prefix)
    product_name: str = Field(alias="productName")  # Product name only (e.g., "Full Search", "Amend Title")
    division_id: int = Field(alias="divisionId")  # Direct=1, Agency=2
    division_name: Optional[str] = Field(None, alias="divisionName")  # "Direct" or "Agency"
    single_seat_count: int = Field(alias="singleSeatCount")
    only_step1_count: int = Field(alias="onlyStep1Count")
    only_step2_count: int = Field(alias="onlyStep2Count")
    total_count: int = Field(alias="totalCount")


class BillingPreviewResponse(BaseModel):
    """Preview billing data before creating report - organization-wide"""
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    details: List[BillingPreviewDetail] = []
    total_files: int = Field(alias="totalFiles")
    pending_orders_count: int = Field(alias="pendingOrdersCount")
    teams_count: int = Field(alias="teamsCount")  # Number of teams included
