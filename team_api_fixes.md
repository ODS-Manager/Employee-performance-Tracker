# Fix for Team Management API Issues

## Issue 1: Fix the list teams endpoint to show states and products

The main issue is in `/Backend/app/api/v1/teams.py` around line 127. The endpoint is using `serialize_team_simple()` which returns empty arrays for states and products.

### Replace lines 150-174 in `/Backend/app/api/v1/teams.py`:

```python
@router.get("")
async def list_teams(
    org_id: Optional[int] = Query(None, alias="orgId", description="Filter by organization"),
    is_active: Optional[bool] = Query(None, alias="isActive", description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List teams with organization-based filtering"""
    
    # Build query with proper eager loading for states, products, and FA names
    query = db.query(Team).options(
        joinedload(Team.states),
        joinedload(Team.products),
        joinedload(Team.fa_names).joinedload(TeamFAName.fa_name)
    )
    
    # Apply role-based filtering
    if current_user.user_role == ROLE_SUPERADMIN:
        if org_id:
            query = query.filter(Team.org_id == org_id)
    elif current_user.user_role in [ROLE_ADMIN, ROLE_TEAM_LEAD, ROLE_EMPLOYEE]:
        # Others can only see their organization's teams
        query = query.filter(Team.org_id == current_user.org_id)
    
    if is_active is not None:
        query = query.filter(Team.is_active == is_active)
    
    teams = query.order_by(Team.name).all()
    
    result = {
        "items": [serialize_team(team) for team in teams],  # Use full serializer instead of simple
        "total": len(teams)
    }
    
    return result
```

## Issue 2: Fix PUT endpoint response

After updating a team, the PUT endpoint should return the updated team data with states and products.

### Update the end of the PUT endpoint (around line 490):

```python
# At the end of the update_team function, before the return statement:
    # Refresh team data with relationships
    db.refresh(team)
    updated_team = db.query(Team).options(
        joinedload(Team.states),
        joinedload(Team.products),
        joinedload(Team.fa_names).joinedload(TeamFAName.fa_name)
    ).filter(Team.id == team_id).first()
    
    return {
        "message": "Team updated successfully",
        "team": serialize_team(updated_team)  # Return full team data
    }
```

## Issue 3: Remove or fix serialize_team_simple function

The `serialize_team_simple` function (around line 177) should either be removed or fixed to actually load the relationships:

### Option A: Remove it entirely (since it's causing issues)

### Option B: Fix it to load relationships:

```python
def serialize_team_simple(team: Team, db: Session) -> dict:
    """Simplified team serialization with basic relationships loaded"""
    # Load relationships if not already loaded
    if not team.states:
        team = db.query(Team).options(
            joinedload(Team.states),
            joinedload(Team.products),
            joinedload(Team.fa_names).joinedload(TeamFAName.fa_name)
        ).filter(Team.id == team.id).first()
    
    return serialize_team(team)  # Use the full serializer
```

## Summary of changes needed:

1. **Replace the list teams query** to include proper eager loading
2. **Change `serialize_team_simple(team)` to `serialize_team(team)`** in the list endpoint  
3. **Update the PUT endpoint response** to return the updated team with relationships
4. **Remove the broken serialize_team_simple function** or fix it

These changes will:
- Fix the empty states/products display in the frontend table
- Ensure PUT requests return proper response data
- Remove the temporary debugging code that's causing issues

The root cause was the temporary fix that disabled relationship loading to debug internal server errors, but this broke the frontend functionality.