# Backend Updates Needed for QR Code Feature

To fully support the QR code functionality, the following backend changes are required:

## 1. Add `short_id` Field to User Model

**File**: `models.py`

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # NEW: Short unique ID for QR codes
    short_id = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 2. Add `short_id` Field to Battery Model

**File**: `models.py`

```python
class Battery(Base):
    __tablename__ = "batteries"

    id = Column(Integer, primary_key=True, index=True)
    hub_id = Column(Integer, ForeignKey("hubs.id"))
    serial_number = Column(String, unique=True, index=True)
    capacity = Column(Integer)  # in Wh
    status = Column(String, default="available")
    model = Column(String, nullable=True)

    # NEW: Short unique ID for QR codes
    short_id = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 3. Auto-generate Short IDs

**File**: `api/app/main.py`

Add a utility function:

```python
def generate_short_id(prefix: str, id_number: int) -> str:
    """
    Generate a short unique ID
    Format: PREFIX-XXXX (e.g., BH-0001, BAT-0023)
    """
    return f"{prefix}-{str(id_number).zfill(4)}"
```

## 4. Update User Creation Endpoint

**File**: `api/app/main.py` - `POST /users/`

```python
@app.post("/users/")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # ... existing validation ...

    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=pwd_context.hash(user.password),
        role=user.role,
        phone=user.phone
    )
    db.add(db_user)
    db.flush()  # Get the ID without committing

    # Generate short ID
    db_user.short_id = generate_short_id("BH", db_user.id)

    db.commit()
    db.refresh(db_user)

    return db_user
```

## 5. Update Battery Creation Endpoint

**File**: `api/app/main.py` - `POST /batteries/`

```python
@app.post("/batteries/")
async def create_battery(battery: BatteryCreate, db: Session = Depends(get_db)):
    # ... existing validation ...

    db_battery = Battery(
        hub_id=battery.hub_id,
        serial_number=battery.serial_number,
        capacity=battery.capacity,
        status=battery.status,
        model=battery.model
    )
    db.add(db_battery)
    db.flush()

    # Generate short ID
    db_battery.short_id = generate_short_id("BAT", db_battery.id)

    db.commit()
    db.refresh(db_battery)

    return db_battery
```

## 6. Add QR Code Lookup Endpoints

**File**: `api/app/main.py`

```python
@app.get("/users/by-short-id/{short_id}")
async def get_user_by_short_id(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by their short ID (from QR code)"""
    user = db.query(User).filter(User.short_id == short_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/batteries/by-short-id/{short_id}")
async def get_battery_by_short_id(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get battery by their short ID (from QR code)"""
    battery = db.query(Battery).filter(Battery.short_id == short_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery
```

## 7. Hub Access Control

Update hub listing to respect user access:

```python
@app.get("/hubs/")
async def list_hubs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List hubs:
    - Superadmin: All hubs
    - Admin/User: Only hubs they have access to
    """
    if current_user.role == "superadmin":
        # Superadmins see all hubs
        hubs = db.query(Hub).all()
    else:
        # Other users see only hubs they have access to
        hubs = db.query(Hub).join(
            UserHubAccess,
            Hub.id == UserHubAccess.hub_id
        ).filter(
            UserHubAccess.user_id == current_user.id
        ).all()

    return hubs
```

## 8. Database Migration

Create Alembic migration:

```bash
alembic revision -m "add_short_id_to_users_and_batteries"
```

**Migration file**:

```python
def upgrade():
    # Add short_id to users table
    op.add_column('users', sa.Column('short_id', sa.String(), nullable=True))
    op.create_index('ix_users_short_id', 'users', ['short_id'], unique=True)

    # Add short_id to batteries table
    op.add_column('batteries', sa.Column('short_id', sa.String(), nullable=True))
    op.create_index('ix_batteries_short_id', 'batteries', ['short_id'], unique=True)

    # Backfill existing users
    connection = op.get_bind()
    users = connection.execute("SELECT id FROM users").fetchall()
    for user in users:
        short_id = f"BH-{str(user[0]).zfill(4)}"
        connection.execute(
            f"UPDATE users SET short_id = '{short_id}' WHERE id = {user[0]}"
        )

    # Backfill existing batteries
    batteries = connection.execute("SELECT id FROM batteries").fetchall()
    for battery in batteries:
        short_id = f"BAT-{str(battery[0]).zfill(4)}"
        connection.execute(
            f"UPDATE batteries SET short_id = '{short_id}' WHERE id = {battery[0]}"
        )


def downgrade():
    op.drop_index('ix_users_short_id', table_name='users')
    op.drop_column('users', 'short_id')
    op.drop_index('ix_batteries_short_id', table_name='batteries')
    op.drop_column('batteries', 'short_id')
```

## 9. Update Pydantic Schemas

**File**: `api/app/main.py`

```python
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    phone: Optional[str] = None
    short_id: Optional[str] = None  # NEW

class BatteryBase(BaseModel):
    hub_id: int
    serial_number: str
    capacity: int
    status: str = "available"
    model: Optional[str] = None
    short_id: Optional[str] = None  # NEW
```

## Summary

After implementing these changes:

1. ✅ Users will have unique short IDs (BH-0001, BH-0002, etc.)
2. ✅ Batteries will have unique short IDs (BAT-0001, BAT-0002, etc.)
3. ✅ QR codes can be scanned to quickly lookup users/batteries
4. ✅ Hub access is properly controlled based on user role
5. ✅ Existing data is migrated with short IDs

**Testing After Implementation:**

```bash
# Test user lookup by short ID
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/users/by-short-id/BH-0001

# Test battery lookup by short ID
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/batteries/by-short-id/BAT-0001

# Test hub listing (should respect user role)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/hubs/
```
