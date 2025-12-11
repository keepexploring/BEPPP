"""
NEW API ENDPOINTS FOR ACCOUNTS & PRICING SYSTEM
This file contains all new endpoints to be added to main.py
"""

# ============================================================================
# SETTINGS API - RENTAL DURATION PRESETS
# ============================================================================

@app.get("/settings/rental-durations",
    tags=["Settings"],
    summary="Get Rental Duration Presets",
    description="Get rental duration presets for a hub (includes global presets)")
async def get_rental_duration_presets(
    hub_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get rental duration presets, hub-specific and global"""
    try:
        from models import RentalDurationPreset

        # Build query
        query = db.query(RentalDurationPreset).filter(
            RentalDurationPreset.is_active == True
        )

        # If hub_id specified, get hub-specific + global
        if hub_id:
            query = query.filter(
                (RentalDurationPreset.hub_id == hub_id) |
                (RentalDurationPreset.hub_id.is_(None))
            )
        # If no hub_id, get global only
        else:
            query = query.filter(RentalDurationPreset.hub_id.is_(None))

        presets = query.order_by(RentalDurationPreset.sort_order).all()

        return {
            "presets": [
                {
                    "preset_id": p.preset_id,
                    "hub_id": p.hub_id,
                    "label": p.label,
                    "duration_value": p.duration_value,
                    "duration_unit": p.duration_unit,
                    "sort_order": p.sort_order,
                    "is_global": p.hub_id is None
                }
                for p in presets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching presets: {str(e)}")


@app.post("/settings/rental-durations",
    tags=["Settings"],
    summary="Create Rental Duration Preset",
    description="Create a new rental duration preset")
async def create_rental_duration_preset(
    label: str,
    duration_value: int,
    duration_unit: str,
    hub_id: Optional[int] = None,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new rental duration preset"""
    from models import RentalDurationPreset

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # ADMIN can only create for their own hub
    if current_user.get('role') == UserRole.ADMIN:
        if hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only create presets for your own hub")

    # Validate duration_unit
    if duration_unit not in ['hours', 'days', 'weeks']:
        raise HTTPException(status_code=400, detail="Invalid duration_unit. Must be: hours, days, or weeks")

    try:
        preset = RentalDurationPreset(
            hub_id=hub_id,
            label=label,
            duration_value=duration_value,
            duration_unit=duration_unit,
            sort_order=sort_order,
            is_active=True
        )

        db.add(preset)
        db.commit()
        db.refresh(preset)

        return {
            "preset_id": preset.preset_id,
            "hub_id": preset.hub_id,
            "label": preset.label,
            "duration_value": preset.duration_value,
            "duration_unit": preset.duration_unit,
            "sort_order": preset.sort_order,
            "message": "Preset created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating preset: {str(e)}")


@app.put("/settings/rental-durations/{preset_id}",
    tags=["Settings"],
    summary="Update Rental Duration Preset",
    description="Update an existing rental duration preset")
async def update_rental_duration_preset(
    preset_id: int,
    label: Optional[str] = None,
    duration_value: Optional[int] = None,
    duration_unit: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a rental duration preset"""
    from models import RentalDurationPreset

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    preset = db.query(RentalDurationPreset).filter(
        RentalDurationPreset.preset_id == preset_id
    ).first()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    # ADMIN can only update their own hub's presets
    if current_user.get('role') == UserRole.ADMIN:
        if preset.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only update presets for your own hub")

    # Validate duration_unit if provided
    if duration_unit and duration_unit not in ['hours', 'days', 'weeks']:
        raise HTTPException(status_code=400, detail="Invalid duration_unit")

    try:
        if label is not None:
            preset.label = label
        if duration_value is not None:
            preset.duration_value = duration_value
        if duration_unit is not None:
            preset.duration_unit = duration_unit
        if sort_order is not None:
            preset.sort_order = sort_order
        if is_active is not None:
            preset.is_active = is_active

        db.commit()
        db.refresh(preset)

        return {
            "preset_id": preset.preset_id,
            "message": "Preset updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating preset: {str(e)}")


@app.delete("/settings/rental-durations/{preset_id}",
    tags=["Settings"],
    summary="Delete Rental Duration Preset",
    description="Delete a rental duration preset")
async def delete_rental_duration_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a rental duration preset"""
    from models import RentalDurationPreset

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    preset = db.query(RentalDurationPreset).filter(
        RentalDurationPreset.preset_id == preset_id
    ).first()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    # ADMIN can only delete their own hub's presets
    if current_user.get('role') == UserRole.ADMIN:
        if preset.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only delete presets for your own hub")

    try:
        db.delete(preset)
        db.commit()
        return {"message": "Preset deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting preset: {str(e)}")


# ============================================================================
# SETTINGS API - PUE TYPES
# ============================================================================

@app.get("/settings/pue-types",
    tags=["Settings"],
    summary="Get PUE Types",
    description="Get PUE equipment types")
async def get_pue_types(
    hub_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get PUE types"""
    try:
        from models import PUEType

        query = db.query(PUEType)

        if hub_id:
            query = query.filter(
                (PUEType.hub_id == hub_id) | (PUEType.hub_id.is_(None))
            )
        else:
            query = query.filter(PUEType.hub_id.is_(None))

        types = query.order_by(PUEType.type_name).all()

        return {
            "types": [
                {
                    "type_id": t.type_id,
                    "type_name": t.type_name,
                    "description": t.description,
                    "hub_id": t.hub_id,
                    "is_global": t.hub_id is None,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in types
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PUE types: {str(e)}")


@app.post("/settings/pue-types",
    tags=["Settings"],
    summary="Create PUE Type",
    description="Create a new PUE equipment type")
async def create_pue_type(
    type_name: str,
    description: Optional[str] = None,
    hub_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new PUE type"""
    from models import PUEType

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # ADMIN can only create for their own hub
    if current_user.get('role') == UserRole.ADMIN:
        if hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only create types for your own hub")

    try:
        pue_type = PUEType(
            type_name=type_name,
            description=description,
            hub_id=hub_id,
            created_by=current_user.get('user_id')
        )

        db.add(pue_type)
        db.commit()
        db.refresh(pue_type)

        return {
            "type_id": pue_type.type_id,
            "type_name": pue_type.type_name,
            "description": pue_type.description,
            "hub_id": pue_type.hub_id,
            "message": "PUE type created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating PUE type: {str(e)}")


@app.put("/settings/pue-types/{type_id}",
    tags=["Settings"],
    summary="Update PUE Type",
    description="Update a PUE equipment type")
async def update_pue_type(
    type_id: int,
    type_name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a PUE type"""
    from models import PUEType

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    pue_type = db.query(PUEType).filter(PUEType.type_id == type_id).first()

    if not pue_type:
        raise HTTPException(status_code=404, detail="PUE type not found")

    # ADMIN can only update their own hub's types
    if current_user.get('role') == UserRole.ADMIN:
        if pue_type.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only update types for your own hub")

    try:
        if type_name is not None:
            pue_type.type_name = type_name
        if description is not None:
            pue_type.description = description

        db.commit()
        return {"message": "PUE type updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating PUE type: {str(e)}")


@app.delete("/settings/pue-types/{type_id}",
    tags=["Settings"],
    summary="Delete PUE Type",
    description="Delete a PUE equipment type")
async def delete_pue_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a PUE type"""
    from models import PUEType

    # Permission check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    pue_type = db.query(PUEType).filter(PUEType.type_id == type_id).first()

    if not pue_type:
        raise HTTPException(status_code=404, detail="PUE type not found")

    # ADMIN can only delete their own hub's types
    if current_user.get('role') == UserRole.ADMIN:
        if pue_type.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only delete types for your own hub")

    try:
        db.delete(pue_type)
        db.commit()
        return {"message": "PUE type deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting PUE type: {str(e)}")
