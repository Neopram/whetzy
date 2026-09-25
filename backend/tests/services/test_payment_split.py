"""Tests for payment split logic (Serie 28.4-28.6).

Verifies:
- Paddle commission: 7.5%
- Split 80/20 (instructor/platform, ADR-45)
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
        # After Paddle: 925, Instructor 80%: 740
        assert result["instructor_gross_cents"] == 740
        assert result["tax_withheld_cents"] == 162  # 740*0.22 = 162.8
        assert result["instructor_net_cents"] == 577  # 740-162.8
        # Platform: 185 (20%) + 162.8 -> 347
        assert result["platform_keep_cents"] == 347

    def test_split_fifty_euros(self):
        """Test split for EUR 50 (5000 cents)."""
        result = PaymentService.calculate_instructor_payout(5000)

        assert result["gross_cents"] == 5000
        assert result["paddle_commission_cents"] == 375  # 5000*0.075
        # After Paddle: 4625, Instructor 80%: 3700
        assert result["instructor_gross_cents"] == 3700
        assert result["tax_withheld_cents"] == 814  # 3700*0.22
        assert result["instructor_net_cents"] == 2886  # 3700-814
        # Platform: 925 (20%) + 814 -> 1739
        assert result["platform_keep_cents"] == 1739

    def test_split_hundred_euros(self):
        """Test split for EUR 100 (10000 cents)."""
        result = PaymentService.calculate_instructor_payout(10000)

        assert result["gross_cents"] == 10000
        assert result["paddle_commission_cents"] == 750  # 7.5%
        # After Paddle: 9250, Instructor 80%: 7400
        assert result["instructor_gross_cents"] == 7400
        assert result["tax_withheld_cents"] == 1628  # 7400*0.22
        assert result["instructor_net_cents"] == 5772  # 7400-1628
        # Platform: 1850 (20%) + 1628 -> 3478
        assert result["platform_keep_cents"] == 3478

    def test_split_thousand_euros(self):
        """Test split for EUR 1000 (100000 cents)."""
        result = PaymentService.calculate_instructor_payout(100000)

        assert result["gross_cents"] == 100000
        assert result["paddle_commission_cents"] == 7500  # 7.5%
        # After Paddle: 92500, Instructor 80%: 74000
        assert result["instructor_gross_cents"] == 74000
        assert result["tax_withheld_cents"] == 16280  # 74000*0.22
        assert result["instructor_net_cents"] == 57720  # 74000-16280
        assert result["platform_keep_cents"] == 34780  # 18500 (20%) + 16280 (tax)

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

    def test_instructor_gets_eighty_percent(self):
        """Verify instructor gets 80% of net after Paddle commission (ADR-45)."""
        result = PaymentService.calculate_instructor_payout(10000)

        # Net after Paddle commission
        net_after_paddle = 10000 - result["paddle_commission_cents"]
        instructor_portion = int(net_after_paddle * 0.80)

        # Instructor gross should be 80% of net
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
