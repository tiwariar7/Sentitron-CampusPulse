from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.db import get_db, Setting, AuditLog, User
from services.auth import get_current_user, RoleChecker
import json

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/")
async def get_settings(
    current_user: User = Depends(RoleChecker(["admin", "moderator", "guest"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Setting))
    settings = result.scalars().all()
    
    audit_logs = []
    if current_user.role == "admin":
        log_result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50))
        audit_logs = log_result.scalars().all()
        
    return {
        "settings": {s.key: json.loads(s.value) for s in settings},
        "audit_logs": audit_logs,
        "role": current_user.role
    }

@router.post("/")
async def update_settings(
    settings_data: dict,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    modified_params = []
    prev_values = {}
    new_values = {}
    
    for key, value in settings_data.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalars().first()
        
        value_str = json.dumps(value)
        
        if setting:
            if setting.value != value_str:
                modified_params.append(key)
                prev_values[key] = json.loads(setting.value)
                new_values[key] = value
                setting.value = value_str
                setting.updated_by = current_user.email
        else:
            modified_params.append(key)
            prev_values[key] = None
            new_values[key] = value
            new_setting = Setting(
                key=key,
                value=value_str,
                description=f"Auto-created setting {key}",
                updated_by=current_user.email
            )
            db.add(new_setting)
            
    if modified_params:
        audit_log = AuditLog(
            administrator_identity=current_user.email,
            user_id=current_user.id,
            action="UPDATE_SETTINGS",
            modified_parameters=json.dumps(modified_params),
            previous_values=json.dumps(prev_values),
            updated_values=json.dumps(new_values)
        )
        db.add(audit_log)
        await db.commit()
        
    return {"status": "success", "modified_keys": modified_params}
