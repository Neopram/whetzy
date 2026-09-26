"""Privacy endpoints — CCPA/CPRA opt-out and data-disclosure (21.3).

Provides:
- POST /privacy/ccpa-opt-out  — record CCPA "Do Not Sell/Share" opt-out
- GET  /privacy/ccpa-disclosure — categories of PI collected & shared (CCPA §1798.100)
- GET  /privacy/rights         — jurisdiction-aware rights summary
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class CcpaOptOutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ccpa_opt_out: bool


class CcpaDisclosure(BaseModel):
    categories_collected: list[str]
    categories_shared: list[str]
    business_purpose: list[str]
    sale_of_data: str
    right_to_delete: str
    right_to_know: str
    right_to_opt_out: str
    non_discrimination: str


class PrivacyRights(BaseModel):
    jurisdiction_note: str
    rights: list[str]
    data_export_url: str
    delete_account_url: str
    contact: str


@router.post(
    "/ccpa-opt-out",
    response_model=CcpaOptOutResponse,
    summary="CCPA Do Not Sell/Share opt-out",
)
async def ccpa_opt_out(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CcpaOptOutResponse:
    """Record the user's CCPA opt-out of sale/sharing of personal information."""
    current_user.ccpa_opt_out = True
    await db.commit()
    await db.refresh(current_user)
    return CcpaOptOutResponse(ccpa_opt_out=current_user.ccpa_opt_out)


@router.delete(
    "/ccpa-opt-out",
    response_model=CcpaOptOutResponse,
    summary="Revoke CCPA opt-out (opt back in)",
)
async def ccpa_opt_in(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CcpaOptOutResponse:
    """Revoke a previous CCPA opt-out."""
    current_user.ccpa_opt_out = False
    await db.commit()
    await db.refresh(current_user)
    return CcpaOptOutResponse(ccpa_opt_out=current_user.ccpa_opt_out)


@router.get(
    "/ccpa-disclosure",
    response_model=CcpaDisclosure,
    summary="CCPA data-collection disclosure (§1798.100)",
)
async def ccpa_disclosure() -> CcpaDisclosure:
    """Public endpoint — no auth required. Returns the categories of personal
    information Whetzy collects and with whom it is shared, as required by
    CCPA/CPRA §1798.100."""
    return CcpaDisclosure(
        categories_collected=[
            "Identifiers (email, username, display name)",
            "Internet/network activity (session duration, feature usage, anonymized)",
            "Education information (quiz responses, skill mastery, progress)",
            "Geolocation (timezone, language preference — no precise location)",
            "Device information (type, OS version, app version)",
        ],
        categories_shared=[
            (
                "Identifiers — with infrastructure providers (Railway, Cloudflare) "
                "under data processing agreements"
            ),
            "Payment data — with Stripe for billing only",
            "Question context (no PII) — with Groq for AI tutor explanations",
        ],
        business_purpose=[
            "Providing adaptive learning services",
            "Processing payments",
            "Improving question quality and learning outcomes",
            "Account security and fraud prevention",
        ],
        sale_of_data="Whetzy does NOT sell personal information to third parties.",
        right_to_delete="You may delete your account and all associated data at any "
        "time via Settings > Delete Account or by emailing support@whetzy.com.",
        right_to_know="You may request a copy of all personal information we hold "
        "about you via GET /api/v1/export/data or by emailing support@whetzy.com.",
        right_to_opt_out="You may opt out of the sale or sharing of personal "
        "information via POST /api/v1/privacy/ccpa-opt-out. Whetzy does not sell data, "
        "but this endpoint is provided for CCPA/CPRA compliance.",
        non_discrimination="Whetzy will not discriminate against you for exercising "
        "your CCPA/CPRA rights. You will receive the same service and pricing.",
    )


@router.get(
    "/rights",
    response_model=PrivacyRights,
    summary="Jurisdiction-aware privacy rights summary",
)
async def privacy_rights() -> PrivacyRights:
    """Public endpoint. Returns a summary of user privacy rights across
    applicable jurisdictions (GDPR, CCPA, UK GDPR)."""
    return PrivacyRights(
        jurisdiction_note=(
            "Your rights depend on where you are located. Whetzy respects the "
            "strongest applicable standard regardless of your location."
        ),
        rights=[
            "Right to access your personal data (GDPR Art. 15 / CCPA §1798.100)",
            "Right to rectification of inaccurate data (GDPR Art. 16)",
            "Right to erasure / deletion (GDPR Art. 17 / CCPA §1798.105)",
            "Right to data portability (GDPR Art. 20 / CCPA §1798.100)",
            "Right to restrict processing (GDPR Art. 18)",
            "Right to object to processing (GDPR Art. 21)",
            "Right to opt out of sale/sharing of PI (CCPA §1798.120)",
            "Right to non-discrimination for exercising rights (CCPA §1798.125)",
            "Right to lodge a complaint with a supervisory authority (GDPR Art. 77)",
        ],
        data_export_url="/api/v1/export/data",
        delete_account_url="/api/v1/auth/me/account",
        contact="support@whetzy.com",
    )
