"""
Billing API Endpoints
Admin and SuperAdmin only access
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from io import BytesIO
from app.database import get_db
from app.models.user import User
from app.schemas.billing import (
    BillingReportCreate,
    BillingReportResponse,
    BillingReportListResponse,
    BillingReportFinalize,
    BillingPreviewRequest,
    BillingPreviewResponse
)
from app.services import billing_service
from app.core.dependencies import require_admin

router = APIRouter()


@router.get("", response_model=BillingReportListResponse)
def list_billing_reports(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    org_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List organization-wide billing reports with optional filters
    No team filtering - all reports are org-wide
    Admin/SuperAdmin only
    
    For superadmin: Can provide orgId as query param to filter by org
    For admin: Uses current user's org_id
    """
    # Determine which org_id to use
    if current_user.org_id is None:
        # Superadmin - use provided org_id or None to get all
        target_org_id = org_id
    else:
        # Regular admin - always use their org_id
        target_org_id = current_user.org_id
    
    reports = billing_service.get_billing_reports(
        db=db,
        org_id=target_org_id,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    
    return BillingReportListResponse(
        items=reports,
        total=len(reports)
    )


@router.get("/{report_id}", response_model=BillingReportResponse)
def get_billing_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get a single billing report by ID
    Admin/SuperAdmin only
    """
    report = billing_service.get_billing_report_by_id(db, report_id)
    
    # Verify access - superadmin can access any, admin only their org
    if current_user.org_id is not None and report.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return report


@router.post("/preview", response_model=BillingPreviewResponse)
def preview_billing(
    request: BillingPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Preview billing data before generating report
    Shows what will be included without creating the report
    Admin/SuperAdmin only
    
    For superadmin: Provide orgId in request body, or defaults to first org
    For admin: Uses current user's org_id
    """
    from app.models.organization import Organization
    
    # Determine which org_id to use
    if current_user.org_id is None:
        # Superadmin - use provided org_id or default to first active org
        if request.org_id is None:
            # Default to first active organization
            first_org = db.query(Organization).filter(
                Organization.is_active == True
            ).first()
            if not first_org:
                raise HTTPException(
                    status_code=400,
                    detail="No active organizations found. Please provide orgId."
                )
            target_org_id = first_org.id
        else:
            target_org_id = request.org_id
    else:
        # Regular admin - use their org_id
        target_org_id = current_user.org_id
    
    return billing_service.preview_billing_data(
        db=db,
        org_id=target_org_id,
        request=request
    )


@router.post("", response_model=BillingReportResponse)
def create_billing_report(
    data: BillingReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create organization-wide billing report grouped by product types
    Admin/SuperAdmin only
    
    For superadmin: Provide orgId in request body, or defaults to first org
    For admin: Uses current user's org_id
    """
    from app.models.organization import Organization
    
    # Determine which org_id to use
    if current_user.org_id is None:
        # Superadmin - use provided org_id or default to first active org
        if data.org_id is None:
            # Default to first active organization
            first_org = db.query(Organization).filter(
                Organization.is_active == True
            ).first()
            if not first_org:
                raise HTTPException(
                    status_code=400,
                    detail="No active organizations found. Please provide orgId."
                )
            target_org_id = first_org.id
        else:
            target_org_id = data.org_id
    else:
        # Regular admin - use their org_id
        target_org_id = current_user.org_id
    
    return billing_service.create_billing_report(
        db=db,
        org_id=target_org_id,
        current_user_id=current_user.id,
        data=data
    )


@router.post("/{report_id}/finalize", response_model=BillingReportResponse)
def finalize_billing_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Finalize a billing report
    - Marks report as 'finalized'
    - Updates all associated orders from 'pending' to 'done'
    Admin/SuperAdmin only
    """
    # Get report to verify org
    report = billing_service.get_billing_report_by_id(db, report_id)
    
    # Verify access - superadmin can access any, admin only their org
    if current_user.org_id is not None and report.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return billing_service.finalize_billing_report(
        db=db,
        report_id=report_id,
        current_user_id=current_user.id
    )


@router.delete("/{report_id}")
def delete_billing_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a billing report (only if in draft status)
    Admin/SuperAdmin only
    """
    # Get report to verify org
    report = billing_service.get_billing_report_by_id(db, report_id)
    
    # Verify access - superadmin can access any, admin only their org
    if current_user.org_id is not None and report.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    billing_service.delete_billing_report(db, report_id)
    
    return {"message": "Billing report deleted successfully"}


@router.get("/{report_id}/export/excel")
def export_billing_report_excel(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Export billing report to Excel format
    Admin/SuperAdmin only
    """
    # Get report to verify org
    report = billing_service.get_billing_report_by_id(db, report_id)
    
    # Verify access - superadmin can access any, admin only their org
    if current_user.org_id is not None and report.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate Excel file
    excel_file = billing_service.export_billing_report_to_excel(db, report_id)
    
    # Create consistent filename
    filename = "Billing_Report.xlsx"
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
