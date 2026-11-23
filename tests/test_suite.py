"""Test runner executável via standard library unittest."""

import unittest
from tests.test_filters import (
    test_spam_detection,
    test_excessive_proposals_rejected,
    test_unrealistic_scope_budget_rejected,
    test_valid_project_accepted,
    test_sniper_target_stack_bonus,
    test_out_of_scope_discard,
    test_fast_delivery_bonus,
)
from tests.test_pricing import test_pricing_calculation_with_discount, test_pricing_min_floor
from tests.test_proposals import test_proposal_generation


class TestBotSuite(unittest.TestCase):
    def test_filter_spam(self):
        test_spam_detection()

    def test_filter_proposals(self):
        test_excessive_proposals_rejected()

    def test_filter_unrealistic(self):
        test_unrealistic_scope_budget_rejected()

    def test_filter_valid(self):
        test_valid_project_accepted()

    def test_filter_sniper_bonus(self):
        test_sniper_target_stack_bonus()

    def test_filter_out_of_scope(self):
        test_out_of_scope_discard()

    def test_filter_fast_delivery(self):
        test_fast_delivery_bonus()

    def test_pricing_calc(self):
        test_pricing_calculation_with_discount()

    def test_pricing_floor(self):
        test_pricing_min_floor()

    def test_proposal_gen(self):
        test_proposal_generation()


if __name__ == "__main__":
    unittest.main()
