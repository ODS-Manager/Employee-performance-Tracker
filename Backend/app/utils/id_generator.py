"""
ID Generation Utilities
Auto-generate unique IDs for users
"""
from sqlalchemy.orm import Session
from app.models.user import User


def generate_examiner_id(db: Session) -> str:
    """
    Auto-generate unique examiner_id in format: USR{sequence:06d}
    Example: USR000001, USR000002, etc.
    
    Args:
        db: Database session
        
    Returns:
        str: Generated examiner_id
    """
    # Find highest sequence number
    last_user = db.query(User).filter(
        User.examiner_id.like('USR%')
    ).order_by(User.examiner_id.desc()).first()
    
    if last_user and last_user.examiner_id:
        try:
            # Extract sequence number from last examiner_id
            last_seq = int(last_user.examiner_id.replace('USR', ''))
            next_seq = last_seq + 1
        except ValueError:
            # If parsing fails, start from 1
            next_seq = 1
    else:
        # No existing users with USR prefix, start from 1
        next_seq = 1
    
    # Generate new examiner_id
    return f"USR{next_seq:06d}"
