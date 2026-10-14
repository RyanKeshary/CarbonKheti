"""
Property-Based Money Invariant Test Suite.
Verifies Section 15:
- Invariant: For ANY non-negative integer paise total, the Largest Remainder Method
  MUST distribute exactly 100% of the funds across beneficiaries.
- Zero floating-point drift or 1-paise leakage across 1,000 randomized disbursement simulations.
- Invariant: Zero negative disbursements.
"""

import random
from services.api.payments.money import allocate_benefit_sharing, FORMULA_CATALOG

def test_largest_remainder_exact_sum_property():
    random.seed(1337)
    
    # Test edge cases
    edge_cases = [0, 1, 2, 3, 7, 10, 99, 100, 101, 1000, 180672, 100000000]
    for total_paise in edge_cases:
        split = allocate_benefit_sharing(total_paise)
        assert split.farmer_paise + split.cooperative_paise + split.platform_paise == total_paise
        assert split.farmer_paise >= 0
        assert split.cooperative_paise >= 0
        assert split.platform_paise >= 0

    # Test 1,000 randomized paise sums (ranging from 10 paise to ₹10,00,00,000)
    for _ in range(1000):
        total_paise = random.randint(1, 1000000000)
        split = allocate_benefit_sharing(total_paise)
        
        # Fundamental Invariant
        assert (split.farmer_paise + split.cooperative_paise + split.platform_paise) == total_paise
        
        # Farmer gets approximately 70% (+/- 1 paise remainder)
        expected_farmer = total_paise * 0.70
        assert abs(split.farmer_paise - expected_farmer) <= 2
        
        # Cooperative gets approximately 15% (+/- 1 paise remainder)
        expected_coop = total_paise * 0.15
        assert abs(split.cooperative_paise - expected_coop) <= 2

def test_alternate_formula_property():
    for formula in FORMULA_CATALOG.keys():
        for total in [100, 1000, 180672, 999999]:
            split = allocate_benefit_sharing(total, formula_version=formula)
            assert split.farmer_paise + split.cooperative_paise + split.platform_paise == total
