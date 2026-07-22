from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import TRIAL_DAYS
from core.deployment import DeploymentConfig, Edition, load_preset_for_edition
from models.tenant import Tenant

TENANT_STATUS_TRIAL = "trial"
TENANT_STATUS_ACTIVE = "active"
TENANT_STATUS_SUSPENDED = "suspended"

def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def build_trial_tenant(*, slug: str, edition: Edition) -> Tenant:
    preset: DeploymentConfig = load_preset_for_edition(edition)
    now = datetime.now(timezone.utc)
    return Tenant(
        slug=slug,
        edition=preset.edition.value,
        locale=preset.locale.value,
        roles_enabled=list(preset.roles_enabled),
        modules=preset.modules.model_dump(),
        dashboard_layout=list(preset.dashboard_layout),
        status=TENANT_STATUS_TRIAL,
        trial_ends_at=now + timedelta(days=TRIAL_DAYS),
    )

def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
    return db.scalar(select(Tenant).where(Tenant.slug == slug))

def assert_tenant_access(tenant: Tenant) -> None:
    if tenant.status == TENANT_STATUS_SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_suspended",
        )
    if tenant.status == TENANT_STATUS_TRIAL:
        if tenant.trial_ends_at is None or _as_utc(tenant.trial_ends_at) <= datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="trial_expired",
            )
