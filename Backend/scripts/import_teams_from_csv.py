"""
Import teams, states, and product types from CSV file
"""
import sys
import os
import csv
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.team import Team, TeamState, TeamProduct
from app.models.organization import Organization


def parse_csv_field(field: str) -> list[str]:
    """Parse CSV field that may contain comma-separated values"""
    # Remove quotes and split by comma
    return [item.strip() for item in field.split(',') if item.strip()]


def import_teams_from_csv(csv_path: str, org_id: int = 1):
    """
    Import teams from CSV file
    
    Args:
        csv_path: Path to CSV file
        org_id: Organization ID to assign teams to (default: 1)
    """
    db = SessionLocal()
    
    try:
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            print(f"Error: Organization with ID {org_id} not found!")
            print("Creating default organization...")
            org = Organization(
                id=org_id,
                name="Default Organization",
                code="DEFAULT",
                is_active=True
            )
            db.add(org)
            db.commit()
            print(f"Created organization: {org.name}")
        else:
            print(f"Using organization: {org.name} (ID: {org.id})")
        
        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            teams_created = 0
            teams_skipped = 0
            
            for row in reader:
                team_name = row['Team Name'].strip()
                states_str = row['State'].strip()
                products_str = row['Product Type'].strip()
                
                # Check if team already exists
                existing_team = db.query(Team).filter(
                    Team.name == team_name,
                    Team.org_id == org_id
                ).first()
                
                if existing_team:
                    print(f"⚠️  Team '{team_name}' already exists, skipping...")
                    teams_skipped += 1
                    continue
                
                # Parse states and products
                states = parse_csv_field(states_str)
                products = parse_csv_field(products_str)
                
                # Create team
                team = Team(
                    name=team_name,
                    org_id=org_id,
                    is_active=True,
                    daily_target=10,
                    monthly_target=None,
                    single_seat_score=1.0,
                    step1_score=0.5,
                    step2_score=0.5
                )
                db.add(team)
                db.flush()  # Get team ID
                
                # Add states
                for state in states:
                    team_state = TeamState(
                        team_id=team.id,
                        state=state
                    )
                    db.add(team_state)
                
                # Add products
                for product in products:
                    team_product = TeamProduct(
                        team_id=team.id,
                        product_type=product
                    )
                    db.add(team_product)
                
                db.commit()
                
                print(f"✅ Created team '{team_name}' with {len(states)} state(s) and {len(products)} product(s)")
                teams_created += 1
            
            print(f"\n{'='*60}")
            print(f"Import Summary:")
            print(f"  Teams created: {teams_created}")
            print(f"  Teams skipped: {teams_skipped}")
            print(f"{'='*60}")
            
            # Show all unique product types
            all_products = db.query(TeamProduct.product_type).distinct().order_by(TeamProduct.product_type).all()
            print(f"\nTotal unique product types in database: {len(all_products)}")
            print("Product Types:")
            for i, (product,) in enumerate(all_products, 1):
                print(f"  {i}. {product}")
            
    except Exception as e:
        print(f"Error importing teams: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Get CSV path (going up to project root)
    csv_path = Path(__file__).parent.parent.parent / "ODS - Team Creation.csv"
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    print(f"Importing teams from: {csv_path}")
    print(f"{'='*60}\n")
    
    # Import teams (defaults to org_id=1)
    import_teams_from_csv(str(csv_path), org_id=1)
    
    print("\n✅ Import completed successfully!")
