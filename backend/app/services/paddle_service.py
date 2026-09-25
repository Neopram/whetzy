"""Paddle integration service (H.29 - Merchant of Record).

Handles Paddle API calls, webhook verification, and payout management.
"""

import hashlib
import hmac
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaddleService:
    """Paddle MoR integration for subscriptions and instructor payouts."""

    @staticmethod
    def verify_webhook_signature(
        raw_payload: bytes,
        signature: str,
        secret: str | None = None,
    ) -> bool:
        """Verify Paddle webhook signature (HMAC-SHA256).

        Paddle sends a signature in the webhook header to ensure authenticity.
        Formula: HMAC-SHA256(secret, body) in hex format.

        Args:
            raw_payload: Raw request body (bytes)
            signature: X-Signature header value from Paddle
            secret: Webhook secret (uses PADDLE_WEBHOOK_SECRET if not provided)

        Returns:
            True if signature is valid
        """
        secret = secret or settings.PADDLE_WEBHOOK_SECRET
        if not secret:
            logger.warning("PADDLE_WEBHOOK_SECRET not configured; skipping verification")
            return False

        # Compute HMAC-SHA256 of the payload
        computed_signature = hmac.new(
            secret.encode(),
            raw_payload,
            hashlib.sha256,
        ).hexdigest()

        # Compare in constant time to prevent timing attacks
        return hmac.compare_digest(computed_signature, signature)

    @staticmethod
    def parse_webhook_payload(raw_payload: bytes) -> dict[str, Any]:
        """Parse and validate webhook payload.

        Returns:
            dict with keys: event_id, event_type, occurred_at, data
        """
        try:
            payload = json.loads(raw_payload.decode("utf-8"))
            return {
                "event_id": payload.get("event_id"),
                "event_type": payload.get("event_type"),
                "occurred_at": payload.get("occurred_at"),
                "data": payload.get("data", {}),
            }
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.exception("Failed to parse Paddle webhook payload")
            raise ValueError(f"Invalid webhook payload: {e}") from e

    @staticmethod
    def calculate_payout_amount(
        gross_cents: int,
        paddle_commission_percent: float = 7.5,
        instructor_share_percent: float = 80.0,
        tax_rate_percent: float = 22.0,
    ) -> dict[str, int]:
        """Calculate instructor payout from gross amount.

        H.29 decision: Paddle is merchant, takes 7.5% commission.
        Remaining split 80/20 between instructor and platform (ADR-41).
        Instructor is taxed at 22% (Grecia).

        Args:
            gross_cents: Amount student paid in cents
            paddle_commission_percent: Paddle's cut (7.5%)
            instructor_share_percent: Instructor's cut of net (80%, ADR-41)
            tax_rate_percent: Tax on instructor earnings (22%)

        Returns:
            {
                'gross_cents': original amount,
                'paddle_commission_cents': amount Paddle keeps,
                'platform_keep_cents': platform share + tax collected,
                'instructor_gross_cents': before tax,
                'tax_withheld_cents': tax amount,
                'instructor_net_cents': final payout amount
            }
        """
        from decimal import Decimal

        gross = Decimal(gross_cents)
        paddle_cut = (Decimal(paddle_commission_percent) / 100) * gross
        after_paddle = gross - paddle_cut

        instructor_cut = (Decimal(instructor_share_percent) / 100) * after_paddle
        platform_cut = after_paddle - instructor_cut

        tax = (Decimal(tax_rate_percent) / 100) * instructor_cut
        instructor_net = instructor_cut - tax

        return {
            "gross_cents": int(gross),
            "paddle_commission_cents": int(paddle_cut),
            "platform_keep_cents": int(platform_cut + tax),
            "instructor_gross_cents": int(instructor_cut),
            "tax_withheld_cents": int(tax),
            "instructor_net_cents": int(instructor_net),
        }
