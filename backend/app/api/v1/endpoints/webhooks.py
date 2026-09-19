"""Paddle webhook endpoints (Serie 28.7).

Handles incoming Paddle events:
- subscription.created
- subscription.updated  
- payout.completed
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.paddle_service import PaddleService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/paddle", status_code=status.HTTP_200_OK)
async def handle_paddle_webhook(
    request: Request,
) -> dict[str, bool]:
    """Receive and process Paddle webhook events.

    Paddle calls this endpoint directly; no JWT auth needed.
    Security: HMAC-SHA256 signature verification via X-Signature header.
    """
    try:
        raw_payload = await request.body()
        signature = request.headers.get("x-signature", "")

        if not signature:
            logger.warning("Paddle webhook missing X-Signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature"
            )

        if not PaddleService.verify_webhook_signature(raw_payload, signature):
            logger.warning("Paddle webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        payload = PaddleService.parse_webhook_payload(raw_payload)
        event_type = payload.get("event_type", "")
        event_id = payload.get("event_id", "")

        logger.info("Paddle webhook received: %s (event_id: %s)", event_type, event_id)

        # Handle specific event types
        if event_type == "subscription.created":
            # TODO: 28.7 - Grant credits to user
            logger.info("Handle subscription.created: %s", event_id)
        elif event_type == "subscription.updated":
            # TODO: 28.7 - Track plan change
            logger.info("Handle subscription.updated: %s", event_id)
        elif event_type == "payout.completed":
            # TODO: 28.7 - Mark instructor payout as completed
            logger.info("Handle payout.completed: %s", event_id)
        else:
            logger.debug("Unhandled Paddle event type: %s", event_type)

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing Paddle webhook")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        ) from e
