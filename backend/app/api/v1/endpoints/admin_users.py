"""Back-office de soporte: buscar usuarios y abrir su ficha (44.1, `docs/PLAN_BACKOFFICE.md`).

Solo el dueño (B1) y solo con la verificación en dos pasos activa (B7). El
listado enmascara el email (B2); la ficha (B3) sí lo da, para «copiar email»
(B8), y abrirla queda en `admin_action_log` como `view` (B6). Nunca se ve ni se
cambia una contraseña, ni se entra como el usuario (B5). Las cinco acciones
sobre la cuenta (B4, 44.2) exigen motivo y dejan su fila en el registro.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.v1.endpoints.admin import require_owner
from app.api.v1.endpoints.auth import require_outbound_email, send_verification_link
from app.core.db import get_db
from app.core.security import user_has_2fa
from app.core.security_middleware import client_ip
from app.models.admin import AdminActionLog, GDPRRequest
from app.models.auth import AuditLog, LoginAttempt, RefreshToken
from app.models.exam import CertificationPurchase
from app.models.session import Response, StudySession
from app.models.user import User, UserSkillState

router = APIRouter()
# `GET /admin/action-log`: la pestaña «Registro» (44.3). Router aparte porque
# `/admin/users/{user_id}` se tragaría `/admin/users/log`.
log_router = APIRouter()

PAGE_SIZE = 20
RECENT_EVENTS = 10
MAX_GRANT_DAYS = 90


async def require_owner_2fa(
    user: User = Depends(require_owner), db: AsyncSession = Depends(get_db)
) -> User:
    """B7: el back-office ve datos de personas; sin segundo factor, no se abre."""
    if not await user_has_2fa(user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="2fa_required")
    return user


def mask_email(email: str) -> str:
    """`federica@gmail.com` → `fe***@gmail.com`; con locales de 1–2 letras, solo la primera."""
    local, _, domain = email.partition("@")
    keep = 2 if len(local) > 2 else 1
    return f"{local[:keep]}***@{domain}"


def _status(u: User) -> Literal["active", "suspended"]:
    return "active" if u.is_active else "suspended"


class UserListItem(BaseModel):
    id: uuid.UUID
    username: str
    email_masked: str
    created_at: datetime
    status: Literal["active", "suspended"]


class UserListPage(BaseModel):
    items: list[UserListItem]
    page: int
    page_size: int
    total: int


@router.get("", response_model=UserListPage)
async def search_users(
    q: str = Query(min_length=3, max_length=100),
    page: int = Query(default=1, ge=1, le=1000),
    _: User = Depends(require_owner_2fa),
    db: AsyncSession = Depends(get_db),
) -> UserListPage:
    """B2: por email, usuario o prefijo de id. La búsqueda no se registra: no abre a nadie."""
    term = q.strip().lower()
    like = f"%{term.replace('%', r'\%').replace('_', r'\_')}%"
    match = or_(
        func.lower(User.email).like(like, escape="\\"),
        func.lower(User.username).like(like, escape="\\"),
        func.lower(cast(User.id, String)).like(f"{term}%"),
    )
    total = await db.scalar(select(func.count()).select_from(User).where(match)) or 0
    rows = (
        await db.execute(
            select(User)
            .where(match)
            .order_by(User.created_at.desc(), User.id)
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
        )
    ).scalars().all()
    return UserListPage(
        items=[
            UserListItem(
                id=u.id, username=u.username, email_masked=mask_email(u.email),
                created_at=u.created_at, status=_status(u),
            )
            for u in rows
        ],
        page=page,
        page_size=PAGE_SIZE,
        total=total,
    )


@router.get("/{user_id}")
async def user_detail(
    user_id: uuid.UUID,
    request: Request,
    owner: User = Depends(require_owner_2fa),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """B3: la ficha. Abrirla deja una fila `view` en el registro (B6)."""
    u = await db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    skills_practiced = await db.scalar(
        select(func.count()).select_from(UserSkillState).where(
            UserSkillState.user_id == u.id, UserSkillState.attempts > 0
        )
    ) or 0
    answers = await db.scalar(
        select(func.count())
        .select_from(Response)
        .join(StudySession, StudySession.id == Response.session_id)
        .where(StudySession.user_id == u.id)
    ) or 0
    purchases = (
        await db.execute(
            select(CertificationPurchase.track_id, CertificationPurchase.source, CertificationPurchase.created_at)
            .where(CertificationPurchase.user_id == u.id)
            .order_by(CertificationPurchase.created_at.desc())
        )
    ).all()
    events = (
        await db.execute(
            select(AuditLog.action, AuditLog.result, AuditLog.timestamp)
            .where(AuditLog.user_id == u.id)
            .order_by(AuditLog.timestamp.desc())
            .limit(RECENT_EVENTS)
        )
    ).all()
    gdpr = (
        await db.execute(
            select(GDPRRequest.request_type, GDPRRequest.status, GDPRRequest.created_at)
            .where(GDPRRequest.user_id == u.id, GDPRRequest.status == "pending")
            .order_by(GDPRRequest.created_at.desc())
        )
    ).all()

    db.add(AdminActionLog(actor_id=owner.id, target_user_id=u.id, action="view", ip=client_ip(request)))
    await db.commit()

    return {
        "id": str(u.id),
        "account": {
            "username": u.username,
            "display_name": u.display_name,
            "email": u.email,
            "email_verified": u.email_verified,
            "language": u.language,
            "status": _status(u),
            "role": u.role,
            "created_at": u.created_at,
            "last_active": u.last_active,
        },
        "plan": {
            "subscription_tier": u.subscription_tier,
            "subscription_status": u.subscription_status,
            "subscription_expires_at": u.subscription_expires_at,
            "subscription_provider": u.subscription_provider,
            "paddle_subscription_id": u.paddle_subscription_id,
            "granted_tier": u.granted_tier,
            "granted_tier_expires_at": u.granted_tier_expires_at,
            "certification_purchases": [
                {"track_id": p.track_id, "source": p.source, "created_at": p.created_at} for p in purchases
            ],
        },
        "progress": {
            "target_track_id": u.target_track_id,
            "target_certification_id": u.target_certification_id,
            "skills_practiced": skills_practiced,
            "answers": answers,
            "level": u.level,
            "current_streak": u.current_streak,
        },
        "security": {
            "recent_events": [
                {"action": e.action, "result": e.result, "timestamp": e.timestamp} for e in events
            ],
        },
        "gdpr": {
            "pending": [
                {"type": g.request_type, "status": g.status, "created_at": g.created_at} for g in gdpr
            ],
        },
    }


# ── B4: acciones (44.2) ──────────────────────────────────────────────────────

Action = Literal["resend_verification", "close_sessions", "unlock", "grant_plan", "suspend", "reactivate"]


class ActionRequest(BaseModel):
    reason: str = Field(max_length=500)
    # Solo `grant_plan`: plan y días (B4: como mucho 90).
    tier: Literal["plus", "pro"] | None = None
    days: int | None = Field(default=None, ge=1, le=MAX_GRANT_DAYS)

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason is required")
        return v.strip()


async def _close_sessions(db: AsyncSession, u: User) -> None:
    """Invalida los tokens de acceso (`jwt_version`) y revoca los de refresco."""
    u.jwt_version += 1
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == u.id).values(revoked=True))


@router.post("/{user_id}/actions/{action}")
async def user_action(
    user_id: uuid.UUID,
    action: str,
    payload: ActionRequest,
    request: Request,
    owner: User = Depends(require_owner_2fa),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if action not in Action.__args__:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown action")
    u = await db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data: dict[str, Any] = {}
    if action == "resend_verification":
        if u.email_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_verified")
        require_outbound_email()
        await send_verification_link(db, u)
    elif action == "close_sessions":
        await _close_sessions(db, u)
    elif action == "unlock":
        cleared = await db.execute(
            delete(LoginAttempt).where(LoginAttempt.email == u.email, LoginAttempt.success.is_(False))
        )
        data["cleared"] = cleared.rowcount  # type: ignore[attr-defined]
    elif action == "grant_plan":
        if payload.tier is None or payload.days is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="tier and days are required")
        u.granted_tier = payload.tier
        u.granted_tier_expires_at = datetime.now(UTC) + timedelta(days=payload.days)
        data = {"tier": payload.tier, "days": payload.days, "expires_at": u.granted_tier_expires_at.isoformat()}
    elif action == "suspend":
        if u.id == owner.id:
            # Suspenderse a uno mismo cierra la única puerta del back-office.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot_suspend_self")
        u.is_active = False
        await _close_sessions(db, u)
    else:  # reactivate
        u.is_active = True

    db.add(
        AdminActionLog(
            actor_id=owner.id, target_user_id=u.id, action=action, reason=payload.reason,
            data=data or None, ip=client_ip(request),
        )
    )
    await db.commit()
    return {"ok": True, "action": action, "data": data}


# ── B6: leer el registro (44.3) ──────────────────────────────────────────────


@log_router.get("")
async def action_log(
    page: int = Query(default=1, ge=1, le=1000),
    _: User = Depends(require_owner_2fa),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Del más nuevo al más viejo, 20 por página, con el usuario del actor y del afectado."""
    actor = aliased(User)
    target = aliased(User)
    total = await db.scalar(select(func.count()).select_from(AdminActionLog)) or 0
    rows = (
        await db.execute(
            select(AdminActionLog, actor.username, target.username)
            .outerjoin(actor, actor.id == AdminActionLog.actor_id)
            .outerjoin(target, target.id == AdminActionLog.target_user_id)
            .order_by(AdminActionLog.created_at.desc(), AdminActionLog.id.desc())
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
        )
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "created_at": row.created_at,
                "action": row.action,
                "reason": row.reason,
                "data": row.data,
                "actor_username": actor_name,
                "target_user_id": str(row.target_user_id) if row.target_user_id else None,
                "target_username": target_name,
            }
            for row, actor_name, target_name in rows
        ],
        "page": page,
        "page_size": PAGE_SIZE,
        "total": total,
    }
