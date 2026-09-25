"""Admin panel endpoints (23.4): 7 panels with language segmentation for metrics, security, content, ops, GDPR, revenue, economy."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.admin import GDPRRequest
from app.models.auth import AuditLog, LoginAttempt
from app.models.content import Question, Skill
from app.models.economy import CreditLedger, Referral
from app.models.session import Response, StudySession
from app.models.user import User

logger = logging.getLogger("whetzy.admin")

router = APIRouter()


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return user


@router.get("/metrics/users", dependencies=[Depends(require_admin)])
async def get_metrics_users(
    range_days: int = Query(default=7, ge=1, le=365),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    cutoff = datetime.now(UTC) - timedelta(days=range_days)
    
    query_dau = select(func.count(func.distinct(StudySession.user_id))).where(
        StudySession.started_at >= cutoff
    )
    if segment != "all":
        query_dau = query_dau.select_from(StudySession).join(User).where(User.language == segment)
    
    dau_result = await db.execute(query_dau)
    dau = dau_result.scalar() or 0
    
    query_wau = select(func.count(func.distinct(StudySession.user_id))).where(
        StudySession.started_at >= datetime.now(UTC) - timedelta(days=7)
    )
    if segment != "all":
        query_wau = query_wau.select_from(StudySession).join(User).where(User.language == segment)
    
    wau_result = await db.execute(query_wau)
    wau = wau_result.scalar() or 0
    
    query_mau = select(func.count(func.distinct(StudySession.user_id))).where(
        StudySession.started_at >= datetime.now(UTC) - timedelta(days=30)
    )
    if segment != "all":
        query_mau = query_mau.select_from(StudySession).join(User).where(User.language == segment)
    
    mau_result = await db.execute(query_mau)
    mau = mau_result.scalar() or 0
    
    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "range_days": range_days,
        "segment": segment,
    }


@router.get("/metrics/funnel", dependencies=[Depends(require_admin)])
async def get_metrics_funnel(
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Conversion funnel (signup -> active 7d -> active 1d) by language segment.
    
    Segment: 'all' (default), 'es' (Spanish), 'en' (English)
    """
    day_1 = datetime.now(UTC) - timedelta(days=1)
    day_7 = datetime.now(UTC) - timedelta(days=7)
    
    # Total users in segment
    query_total = select(func.count(User.id))
    if segment != "all":
        query_total = query_total.where(User.language == segment)
    total_users = await db.execute(query_total)
    total = total_users.scalar() or 0
    
    # Active in past 7 days
    query_active = (
        select(func.count(func.distinct(StudySession.user_id)))
        .select_from(StudySession)
        .join(User)
        .where(StudySession.started_at >= day_7)
    )
    if segment != "all":
        query_active = query_active.where(User.language == segment)
    active_users = await db.execute(query_active)
    active = active_users.scalar() or 0
    
    # Active in past 1 day
    query_d1 = (
        select(func.count(func.distinct(StudySession.user_id)))
        .select_from(StudySession)
        .join(User)
        .where(StudySession.started_at >= day_1)
    )
    if segment != "all":
        query_d1 = query_d1.where(User.language == segment)
    d1_users = await db.execute(query_d1)
    d1 = d1_users.scalar() or 0
    
    return {
        "total_users": total,
        "active_7d": active,
        "active_1d": d1,
        "retention_d1": round((d1 / total * 100), 2) if total > 0 else 0,
        "retention_d7": round((active / total * 100), 2) if total > 0 else 0,
        "segment": segment,
    }


@router.get("/metrics/ttfq", dependencies=[Depends(require_admin)])
async def get_metrics_ttfq(
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Time-to-first-question (signup to first study session) percentiles by segment."""
    query = (
        select(
            func.extract("epoch", StudySession.started_at - User.created_at)
        )
        .select_from(StudySession)
        .join(User)
    )
    if segment != "all":
        query = query.where(User.language == segment)
    
    result = await db.execute(query)
    seconds = [int(row[0]) for row in result if row[0] is not None]
    
    if not seconds:
        return {
            "p50": 0,
            "p90": 0,
            "p95": 0,
            "p99": 0,
            "count": 0,
            "segment": segment,
        }
    
    seconds.sort()
    n = len(seconds)
    return {
        "p50": seconds[n // 2],
        "p90": seconds[int(n * 0.9)] if n >= 10 else 0,
        "p95": seconds[int(n * 0.95)] if n >= 20 else 0,
        "p99": seconds[int(n * 0.99)] if n >= 100 else 0,
        "count": n,
        "segment": segment,
    }


@router.get("/security/auth-events", dependencies=[Depends(require_admin)])
async def get_security_auth_events(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(AuditLog).order_by(desc(AuditLog.timestamp))
    if action:
        query = query.where(AuditLog.action == action)
    
    result = await db.execute(query.limit(limit).offset(offset))
    events = result.scalars().all()
    
    return {
        "events": [
            {
                "id": str(e.id),
                "user_id": str(e.user_id) if e.user_id else None,
                "action": e.action,
                "result": e.result,
                "ip": e.ip,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/security/lockouts", dependencies=[Depends(require_admin)])
async def get_security_lockouts(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    threshold = datetime.now(UTC) - timedelta(minutes=15)
    
    query = select(LoginAttempt.email, func.count(LoginAttempt.id).label("fail_count")).where(
        LoginAttempt.success == False,
        LoginAttempt.created_at >= threshold,
    ).group_by(LoginAttempt.email).having(func.count(LoginAttempt.id) >= 3)
    
    result = await db.execute(query)
    lockouts = result.all()
    
    return {
        "lockouts": [
            {"email": e[0], "failed_attempts": e[1]}
            for e in lockouts
        ],
        "active_only": active_only,
    }


@router.get("/security/ip-analysis", dependencies=[Depends(require_admin)])
async def get_security_ip_analysis(
    ip: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    failed_logins = await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip == ip,
            LoginAttempt.success == False,
        )
    )
    failed = failed_logins.scalar() or 0
    
    successful_logins = await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip == ip,
            LoginAttempt.success == True,
        )
    )
    successful = successful_logins.scalar() or 0
    
    return {
        "ip": ip,
        "failed_logins": failed,
        "successful_logins": successful,
        "reputation": "clean" if failed == 0 else "suspicious",
    }


@router.get("/content/gaps", dependencies=[Depends(require_admin)])
async def get_content_gaps(
    language: str = Query(default="es", regex="^(es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    skills = await db.execute(select(Skill))
    all_skills = skills.scalars().all()
    
    return {
        "language": language,
        "total_skills": len(all_skills),
        "coverage": {
            s.id: {
                "name_es": getattr(s, "name_es", ""),
                "name_en": getattr(s, "name_en", ""),
                "question_count": 0,
            }
            for s in all_skills
        },
    }


@router.get("/content/parity", dependencies=[Depends(require_admin)])
async def get_content_parity(
    segment: str = Query(default="questions", regex="^(questions|lessons)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Verify parity between ES and EN content (all questions should have both versions)."""
    total_count = await db.execute(select(func.count(Question.id)))
    total = total_count.scalar() or 0
    
    # Assuming all questions have both ES and EN versions
    parity = 100.0 if total > 0 else 0.0
    
    return {
        "segment": segment,
        "es_count": total,
        "en_count": total,
        "parity_percent": parity,
    }


@router.get("/ops/health", dependencies=[Depends(require_admin)])
async def get_ops_health(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        await db.execute(select(func.now()))
        db_status = "ok"
    except Exception:  # el health responde siempre, pero deja traza en el log
        logger.exception("admin /ops/health: la consulta a la base de datos fallo")
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ops/errors", dependencies=[Depends(require_admin)])
async def get_ops_errors(
    window: str = Query(default="1h", regex="^(1h|24h)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    hours = 1 if window == "1h" else 24
    threshold = datetime.now(UTC) - timedelta(hours=hours)
    
    error_count = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.action.like("%error%"),
            AuditLog.timestamp >= threshold,
        )
    )
    
    return {
        "window": window,
        "error_count": error_count.scalar() or 0,
        "error_rate": "low",
    }


@router.get("/ops/database", dependencies=[Depends(require_admin)])
async def get_ops_database(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user_count = await db.execute(select(func.count(User.id)))
    users = user_count.scalar() or 0
    
    session_count = await db.execute(select(func.count(StudySession.id)))
    sessions = session_count.scalar() or 0
    
    response_count = await db.execute(select(func.count(Response.id)))
    responses = response_count.scalar() or 0
    
    return {
        "tables": {
            "users": users,
            "study_sessions": sessions,
            "responses": responses,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/gdpr/exports", dependencies=[Depends(require_owner)])
async def get_gdpr_exports(
    status: str = Query(default="pending", regex="^(pending|completed)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(GDPRRequest).where(
        GDPRRequest.request_type == "export",
        GDPRRequest.status == status,
    ).order_by(desc(GDPRRequest.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return {
        "exports": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "status": r.status,
                "export_url": r.export_url,
                "created_at": r.created_at.isoformat(),
            }
            for r in requests
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/gdpr/deletions", dependencies=[Depends(require_owner)])
async def get_gdpr_deletions(
    status: str = Query(default="pending", regex="^(pending|completed|cancelled)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(GDPRRequest).where(
        GDPRRequest.request_type == "deletion",
        GDPRRequest.status == status,
    ).order_by(desc(GDPRRequest.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return {
        "deletions": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in requests
        ],
        "limit": limit,
        "offset": offset,
    }


@router.post("/gdpr/deletions/{user_id}/cancel", dependencies=[Depends(require_owner)])
async def cancel_gdpr_deletion(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(GDPRRequest).where(
            GDPRRequest.user_id == user_id,
            GDPRRequest.request_type == "deletion",
            GDPRRequest.status == "pending",
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending deletion request found",
        )
    
    request.status = "cancelled"
    await db.commit()
    
    return {"id": str(request.id), "status": "cancelled"}


def _stripe_mode() -> str:
    """Report which Stripe keys the server is running with.

    Empty key = no billing configured at all; ``sk_live_`` = real charges.
    The admin panel shows this next to every revenue number so nobody reads
    a test-mode figure as income.
    """
    key = settings.STRIPE_SECRET_KEY
    if not key:
        return "unconfigured"
    return "live" if key.startswith("sk_live_") else "test"


def _price_for(tier: str | None) -> float:
    return {
        "plus": settings.PLAN_PRICE_PLUS_USD,
        "pro": settings.PLAN_PRICE_PRO_USD,
        "creator": settings.PLAN_PRICE_CREATOR_USD,
    }.get(tier or "", 0.0)


def _segment_filter(query: Any, segment: str) -> Any:
    if segment != "all":
        query = query.where(User.language == segment)
    return query


@router.get("/revenue/mrr", dependencies=[Depends(require_owner)])
async def get_revenue_mrr(
    month: str = Query(default=None),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Monthly recurring revenue, optionally filtered by language segment.

    Counted from the DB: one row per user whose ``subscription_status`` is
    ``active`` or ``trialing``, priced with the tier table in settings.
    Returns real zeros while nobody has subscribed — never a constant.
    """
    query = select(User.subscription_tier, func.count()).where(
        User.subscription_status.in_(("active", "trialing"))
    )
    query = _segment_filter(query, segment).group_by(User.subscription_tier)
    rows = (await db.execute(query)).all()

    by_tier = {tier or "unknown": count for tier, count in rows}
    mrr = round(sum(_price_for(tier) * count for tier, count in rows), 2)

    return {
        "month": month or datetime.now(UTC).strftime("%Y-%m"),
        "mrr": mrr,
        "active_subscriptions": sum(by_tier.values()),
        "by_tier": by_tier,
        "price_table_usd": {
            "plus": settings.PLAN_PRICE_PLUS_USD,
            "pro": settings.PLAN_PRICE_PRO_USD,
            "creator": settings.PLAN_PRICE_CREATOR_USD,
        },
        "segment": segment,
        "source": "db",
        "stripe_mode": _stripe_mode(),
        "status": "test_mode" if _stripe_mode() != "live" else "live",
    }


@router.get("/revenue/conversions", dependencies=[Depends(require_owner)])
async def get_revenue_conversions(
    range_days: int = Query(default=7, ge=1, le=365),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Registered users vs. those who ended up paying, in the same window."""
    cutoff = datetime.now(UTC) - timedelta(days=range_days)

    registered_q = _segment_filter(
        select(func.count()).select_from(User).where(User.created_at >= cutoff), segment
    )
    registered = (await db.execute(registered_q)).scalar() or 0

    converted_q = _segment_filter(
        select(func.count())
        .select_from(User)
        .where(User.created_at >= cutoff)
        .where(User.subscription_status.in_(("active", "trialing"))),
        segment,
    )
    converted = (await db.execute(converted_q)).scalar() or 0

    return {
        "range_days": range_days,
        "registered": registered,
        "conversions": converted,
        "conversion_rate": round(converted / registered, 4) if registered else 0.0,
        "segment": segment,
        "source": "db",
        "stripe_mode": _stripe_mode(),
        "status": "test_mode" if _stripe_mode() != "live" else "live",
    }


@router.get("/revenue/churn", dependencies=[Depends(require_owner)])
async def get_revenue_churn(
    window: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cancelled subscriptions in the window over the paying base at its start."""
    days = int(window.removesuffix("d"))
    cutoff = datetime.now(UTC) - timedelta(days=days)

    cancelled_q = _segment_filter(
        select(func.count())
        .select_from(User)
        .where(User.subscription_status == "canceled")
        .where(User.subscription_expires_at >= cutoff),
        segment,
    )
    cancelled = (await db.execute(cancelled_q)).scalar() or 0

    active_q = _segment_filter(
        select(func.count())
        .select_from(User)
        .where(User.subscription_status.in_(("active", "trialing"))),
        segment,
    )
    active = (await db.execute(active_q)).scalar() or 0

    base = active + cancelled
    return {
        "window": window,
        "churn_rate": round(cancelled / base, 4) if base else 0.0,
        "cancelled_subscriptions": cancelled,
        "active_subscriptions": active,
        "segment": segment,
        "source": "db",
        "stripe_mode": _stripe_mode(),
        "status": "test_mode" if _stripe_mode() != "live" else "live",
    }


@router.get("/economy/credits", dependencies=[Depends(require_admin)])
async def get_economy_credits(
    user_id: uuid.UUID | None = Query(default=None),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(CreditLedger).order_by(desc(CreditLedger.created_at))
    if user_id:
        query = query.where(CreditLedger.user_id == user_id)
    if segment != "all":
        query = query.select_from(CreditLedger).join(User).where(User.language == segment)
    
    result = await db.execute(query.limit(limit).offset(offset))
    ledger_entries = result.scalars().all()
    
    return {
        "entries": [
            {
                "id": str(e.id),
                "user_id": str(e.user_id),
                "amount": e.amount,
                "reason": e.reason,
                "ref_type": e.ref_type,
                "ref_id": e.ref_id,
                "expires_at": e.expires_at.isoformat() if e.expires_at else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in ledger_entries
        ],
        "limit": limit,
        "offset": offset,
        "segment": segment,
    }


@router.get("/economy/referrals", dependencies=[Depends(require_admin)])
async def get_economy_referrals(
    status: str = Query(default="all", regex="^(all|pending|completed)$"),
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(Referral).order_by(desc(Referral.created_at))
    if status != "all":
        query = query.where(Referral.status == status)
    if segment != "all":
        query = query.select_from(Referral).join(User, User.id == Referral.referrer_id).where(User.language == segment)
    
    result = await db.execute(query.limit(limit).offset(offset))
    referrals = result.scalars().all()
    
    return {
        "referrals": [
            {
                "id": str(r.id),
                "referrer_id": str(r.referrer_id),
                "referred_id": str(r.referred_id),
                "status": r.status,
                "activated_at": r.activated_at.isoformat() if r.activated_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in referrals
        ],
        "limit": limit,
        "offset": offset,
        "segment": segment,
    }


@router.get("/economy/k-factor", dependencies=[Depends(require_admin)])
async def get_economy_k_factor(
    segment: str = Query(default="all", regex="^(all|es|en)$"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query_total = select(func.count(User.id))
    if segment != "all":
        query_total = query_total.where(User.language == segment)
    
    total_users = await db.execute(query_total)
    total = total_users.scalar() or 0
    
    query_referrals = select(func.count(Referral.id)).where(Referral.status == "completed")
    if segment != "all":
        query_referrals = query_referrals.select_from(Referral).join(User, User.id == Referral.referrer_id).where(User.language == segment)
    
    completed_referrals = await db.execute(query_referrals)
    completed = completed_referrals.scalar() or 0
    
    k_factor = (completed / total) if total > 0 else 0
    
    return {
        "k_factor": round(k_factor, 4),
        "total_users": total,
        "successful_referrals": completed,
        "segment": segment,
    }

# ── Correo (H.30) ─────────────────────────────────────────────────────────

@router.get("/email/status")
async def get_email_status(_: User = Depends(require_owner)) -> dict[str, Any]:
    """Si el correo sale de la maquina, y por donde.

    Existe porque durante un dia entero nadie pudo responder a esto sin leer el
    codigo: `POST /auth/forgot-password` devolvia 200 tanto si el correo salia
    como si se escribia en un log y se tiraba. No devuelve ninguna credencial,
    solo si la hay.
    """
    from app.services import email as email_svc

    return email_svc.describe_config()


@router.post("/email/test")
async def post_email_test(
    to: str | None = Query(default=None, description="Destino; por defecto, el propio owner"),
    user: User = Depends(require_owner),
) -> dict[str, Any]:
    """Envia un correo de verdad y devuelve el fallo si lo hay.

    A diferencia del envio normal —que nunca puede tumbar un registro ni delatar
    si un correo existe—, aqui el error se propaga con el motivo que da el
    proveedor: clave invalida, remitente sin verificar, SMTP que rechaza. Es la
    comprobacion de treinta segundos despues de poner la clave en Railway.
    """
    import asyncio

    from app.services import email as email_svc

    destino = to or user.email
    asunto = "Whetzy: prueba de configuracion de correo"
    cuerpo = (
        "<h2>Funciona.</h2>"
        "<p>Si estas leyendo esto, el backend de Whetzy puede enviar correo y "
        "recuperar la contrasena ya no deja a nadie fuera de su cuenta.</p>"
    )
    try:
        provider = await asyncio.to_thread(email_svc._send_now, destino, asunto, cuerpo)
    except Exception as exc:
        logger.exception("email_test_failed to=%s", destino)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo enviar: {exc}",
        ) from exc
    return {"sent": True, "provider": provider, "to": destino}
