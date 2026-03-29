"""
Allowed Duplicate Product Model
Manages which product types can have duplicate file numbers
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AllowedDuplicateProduct(Base):
    """
    Model for product types that allow duplicate file numbers.
    
    When a product type is in this table with is_active=True,
    users with elevated roles (superadmin, admin, team_lead) can
    create multiple orders with the same file_number + product_type
    combination within a team.
    """
    __tablename__ = "allowed_duplicate_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_type = Column(String(100), nullable=False, unique=True)  # Normalized product type name
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True)
    modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    modifier = relationship("User", foreign_keys=[modified_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_allowed_dup_product_type', 'product_type'),
        Index('idx_allowed_dup_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<AllowedDuplicateProduct(id={self.id}, product_type='{self.product_type}', is_active={self.is_active})>"
