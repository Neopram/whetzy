"""Tests for payment split logic (Serie 28.4-28.6).

Verifies:
- Paddle commission: 7.5%
- Split 70/30 (instructor/platform)
- Tax withholding: 22% (Grecia)
- Edge cases and decimal precision
"""

import pytest
from decimal import Decimal

from app.services.payment_service import PaymentService
from app.services.paddle_service import PaddleService


class TestPaymentSplit:
    """Test instructor payout split calculation."""

    def test_split_ten_euros(self):
        """Test split for €10 (1000 cents)."""
        result = PaymentService.calculate_instructor_payout(1000)

        assert result["gross_cents"] == 1000
        assert result["paddle_commission_cents"] == 75  # 7.5%
        assert result["instructor_gross_cents"] == 650  # (1000-75)*0.70
        assert result["tax_withheld_cents"] == 143     # 650*0.22
        assert result["instructor_net_cents"] == 507   # 650-143
        assert result["platform_keep_cents"] == 443    # remainder

    def test_split_fifty_euros(self):
        """Test split for €50 (5000 cents)."""
        result = PaymentService.calculate_instructor_payout(5000)

        assert result["gross_cents"] == 5000
        assert result["paddle_commission_cents"] == 375  # 5000*0.075
        assert result["instructor_gross_cents"] == 3250  # (5000-375)*0.70
        # Remainder should equal instructor_gross_cents - instructor_net_cents + remainder
        assert result["instructor_net_cents"] > 0

    def test_split_hundred_euros(self):
        """Test split for €100 (10000 cents)."""
        result = PaymentService.calculate_instructor_payout(10000)

        assert result["gross_cents"] == 10000
        # Verify all components sum to gross
        total = (
            result["paddle_commission_cents"]
            + result["platform_keep_cents"]
            + result["instructor_net_cents"]
        )
        assert total == 10000

    def test_split_thousand_euros(self):
        """Test split for €1000 (100000 cents)."""
        result = PaymentService.calculate_instructor_payout(100000)

        assert result["gross_cents"] == 100000
        assert result["paddle_commission_cents"] == 7500  # 7.5%
        instructor_after_paddle = 100000 - 7500
        assert result["instructor_gross_cents"] == int(instructor_after_paddle * 0.70)
        
    def test_small_amount(self):
        """Test split for €1 (100 cents) - minimum viable."""
        result = PaymentService.calculate_instructor_payout(100)

        assert result["gross_cents"] == 100
        assert result["paddle_commission_cents"] == 7
        assert result["instructor_net_cents"] >= 0  # Can't be negative

    def test_split_components_sum_to_gross(self):
        """Verify split components always sum to gross amount."""
        amounts = [100, 500, 1000, 5000, 10000, 50000]
        
        for amount in amounts:
            result = PaymentService.calculate_instructor_payout(amount)
            total = (
                result["paddle_commission_cents"]
                + result["platform_keep_cents"]
                + result["instructor_net_cents"]
            )
            assert total == amount, f"Split doesn't sum for €{amount/100}"

    def test_instructor_gets_seventy_percent(self):
        """Verify instructor gets 70% of net after Paddle commission."""
        result = PaymentService.calculate_instructor_payout(10000)

        # Net after Paddle commission
        net_after_paddle = 10000 - result["paddle_commission_cents"]
        instructor_portion = net_after_paddle * 0.70
        
        # Instructor gross should be 70% of net
        assert result["instructor_gross_cents"] == int(instructor_portion)

    def test_tax_is_twenty_two_percent(self):
        """Verify tax is 22% of instructor gross (Grecia)."""
        result = PaymentService.calculate_instructor_payout(10000)

        expected_tax = int(result["instructor_gross_cents"] * 0.22)
        assert result["tax_withheld_cents"] == expected_tax


class TestPaddleService:
    """Test Paddle integration service."""

    def test_webhook_signature_verification(self):
        """Test webhook signature verification."""
        import hmac
        import hashlib

        secret = "test_secret"
        payload = b'{"event_id": "123", "event_type": "payout.completed"}'

        # Compute signature
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Verify should pass
        assert PaddleService.verify_webhook_signature(payload, sig, secret)

        # Verify should fail with wrong signature
        assert not PaddleService.verify_webhook_signature(payload, "wrong_sig", secret)

    def test_parse_webhook_payload(self):
        """Test parsing webhook payload."""
        import json

        data = {
            "event_id": "test_123",
            "event_type": "payout.completed",
            "occurred_at": "2026-09-19T14:00:00Z",
            "data": {"payout_id": "payout_123"}
        }
        payload = json.dumps(data).encode("utf-8")

        result = PaddleService.parse_webhook_payload(payload)

        assert result["event_id"] == "test_123"
        assert result["event_type"] == "payout.completed"
        assert result["data"]["payout_id"] == "payout_123"

    def test_calculate_payout_amount(self):
        """Test Paddle payout amount calculation."""
        result = PaddleService.calculate_payout_amount(1000)

        assert result["gross_cents"] == 1000
        assert result["paddle_commission_cents"] == 75
        assert result["instructor_net_cents"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
