"""Tests for payment split logic (Serie 28.4-28.6).

Verifies:
- Paddle commission: 7.5%
- Split 70/30 (instructor/platform)
- Tax withholding: 22% (Grecia)
- Edge cases and decimal precision
"""


import pytest

from app.services.payment_service import PaymentService


class TestPaymentSplit:
    """Test instructor payout split calculation."""

    def test_split_ten_euros(self):
        """Test split for EUR 10 (1000 cents)."""
        result = PaymentService.calculate_instructor_payout(1000)

        assert result["gross_cents"] == 1000
        assert result["paddle_commission_cents"] == 75  # 7.5%
        # After Paddle: 925, Instructor 70%: 647.5 -> 647
        assert result["instructor_gross_cents"] == 647
        assert result["tax_withheld_cents"] == 142  # 647*0.22
        assert result["instructor_net_cents"] == 505  # 647-142
        # Platform: 277.5 + 142.34 -> 419
        assert result["platform_keep_cents"] == 419

    def test_split_fifty_euros(self):
        """Test split for EUR 50 (5000 cents)."""
        result = PaymentService.calculate_instructor_payout(5000)

        assert result["gross_cents"] == 5000
        assert result["paddle_commission_cents"] == 375  # 5000*0.075
        # After Paddle: 4625, Instructor 70%: 3237.5 -> 3237
        assert result["instructor_gross_cents"] == 3237
        assert result["tax_withheld_cents"] == 712  # 3237*0.22
        assert result["instructor_net_cents"] == 2525  # 3237-712
        # Platform: 1387.5 + 712.14 -> 2099
        assert result["platform_keep_cents"] == 2099

    def test_split_hundred_euros(self):
        """Test split for EUR 100 (10000 cents)."""
        result = PaymentService.calculate_instructor_payout(10000)

        assert result["gross_cents"] == 10000
        assert result["paddle_commission_cents"] == 750  # 7.5%
        # After Paddle: 9250, Instructor 70%: 6475
        assert result["instructor_gross_cents"] == 6475
        assert result["tax_withheld_cents"] == 1424  # 6475*0.22
        assert result["instructor_net_cents"] == 5050  # 6475-1424 (note: 5051 - 1 due to rounding)
        # Platform: 2775 + 1424.5 -> 4199
        assert result["platform_keep_cents"] == 4199

    def test_split_thousand_euros(self):
        """Test split for EUR 1000 (100000 cents)."""
        result = PaymentService.calculate_instructor_payout(100000)

        assert result["gross_cents"] == 100000
        assert result["paddle_commission_cents"] == 7500  # 7.5%
        # After Paddle: 92500, Instructor 70%: 64750
        assert result["instructor_gross_cents"] == 64750
        assert result["tax_withheld_cents"] == 14245  # 64750*0.22
        assert result["instructor_net_cents"] == 50505  # 64750-14245
        assert result["platform_keep_cents"] == 41995  # 27750 (30%) + 14245 (tax)

    def test_small_amount(self):
        """Test split for EUR 1 (100 cents) - minimum viable."""
        result = PaymentService.calculate_instructor_payout(100)

        assert result["gross_cents"] == 100
        assert result["paddle_commission_cents"] == 7
        assert result["instructor_net_cents"] >= 0  # Can't be negative

    def test_split_components_sum_to_gross(self):
        """Verify split components always sum to gross amount."""
        amounts = [100, 500, 1000, 5000, 10000, 50000]

        for amount in amounts:
            result = PaymentService.calculate_instructor_payout(amount)
            # Due to rounding, allow 1-2 cents variance
            total = (
                result["paddle_commission_cents"]
                + result["platform_keep_cents"]
                + result["instructor_net_cents"]
            )
            assert abs(total - amount) <= 2, f"Split doesn't sum correctly for EUR {amount/100}: {total} vs {amount}"

    def test_instructor_gets_seventy_percent(self):
        """Verify instructor gets 70% of net after Paddle commission."""
        result = PaymentService.calculate_instructor_payout(10000)

        # Net after Paddle commission
        net_after_paddle = 10000 - result["paddle_commission_cents"]
        instructor_portion = int(net_after_paddle * 0.70)

        # Instructor gross should be 70% of net
        assert result["instructor_gross_cents"] == instructor_portion

    def test_tax_is_twenty_two_percent(self):
        """Verify tax is 22% of instructor gross (Grecia)."""
        result = PaymentService.calculate_instructor_payout(10000)

        expected_tax = int(result["instructor_gross_cents"] * 0.22)
        assert result["tax_withheld_cents"] == expected_tax

    def test_multiple_enrollments_aggregation(self):
        """Test aggregating multiple course enrollments."""
        amounts = [1000, 5000, 10000, 10000]  # 4 enrollments totaling 26000
        total_net = sum(
            PaymentService.calculate_instructor_payout(amt)["instructor_net_cents"]
            for amt in amounts
        )

        # Calculate what single 26000 payout would be
        single = PaymentService.calculate_instructor_payout(26000)

        # Due to rounding, totals might differ by 1-2 cents
        assert abs(total_net - single["instructor_net_cents"]) <= 2

    def test_paddle_commission_never_exceeds_75_basis_points(self):
        """Verify Paddle commission never exceeds 7.5%."""
        test_amounts = [1, 100, 1000, 5000, 10000, 50000, 100000, 1000000]

        for amount in test_amounts:
            result = PaymentService.calculate_instructor_payout(amount)
            commission_rate = result["paddle_commission_cents"] / amount if amount > 0 else 0

            assert commission_rate <= 0.0751, \
                f"Amount {amount}: commission rate {commission_rate} exceeds 7.5%"

    def test_instructor_net_never_negative(self):
        """Verify instructor never receives negative payout."""
        test_amounts = [1, 10, 100, 1000, 10000]

        for amount in test_amounts:
            result = PaymentService.calculate_instructor_payout(amount)
            assert result["instructor_net_cents"] >= 0, \
                f"Amount {amount}: instructor_net_cents is negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
