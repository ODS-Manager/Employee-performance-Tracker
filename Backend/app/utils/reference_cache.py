"""
Reference Data Cache
Previously cached frequently accessed reference data.
Now queries the database directly after caching removal.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
from app.models.reference import OrderStatusType, TransactionType, ProcessType, Division


class ReferenceDataCache:
    """Centralized reference data helpers (caching disabled)"""
    
    @staticmethod
    def get_order_status_id_by_name(name: str, db: Session) -> Optional[int]:
        """
        Get order status ID by name.
        Common usage: getting "Completed" status ID
        """
        status = db.query(OrderStatusType).filter(
            OrderStatusType.name == name
        ).first()
        return status.id if status else None
    
    @staticmethod
    def get_all_order_statuses(db: Session) -> List[Dict[str, Any]]:
        """Get all order statuses."""
        statuses = db.query(OrderStatusType).all()
        return [{"id": s.id, "name": s.name} for s in statuses]
    
    @staticmethod
    def get_transaction_type_id_by_name(name: str, db: Session) -> Optional[int]:
        """Get transaction type ID by name."""
        t_type = db.query(TransactionType).filter(
            TransactionType.name == name
        ).first()
        return t_type.id if t_type else None
    
    @staticmethod
    def get_all_transaction_types(db: Session) -> List[Dict[str, Any]]:
        """Get all transaction types."""
        types = db.query(TransactionType).all()
        return [{"id": t.id, "name": t.name} for t in types]
    
    @staticmethod
    def get_all_process_types(db: Session) -> List[Dict[str, Any]]:
        """Get all process types."""
        types = db.query(ProcessType).all()
        return [{"id": t.id, "name": t.name} for t in types]
    
    @staticmethod
    def get_all_divisions(db: Session) -> List[Dict[str, Any]]:
        """Get all divisions."""
        divisions = db.query(Division).all()
        return [{"id": d.id, "name": d.name} for d in divisions]
    
    @staticmethod
    def invalidate_all_reference_caches() -> None:
        """No-op: reference data caching is disabled."""
        pass
    
    @staticmethod
    def warm_up_cache(db: Session) -> None:
        """No-op: reference data caching is disabled."""
        pass
