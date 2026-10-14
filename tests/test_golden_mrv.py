"""
Golden MRV & Financial Allocation Test Suite.
Verifies Section 2 (Items 1, 2, 3) and Section 15:
- 105-day season, 1.08 ha paddy holding
- Dynamic MRV execution matches Verra VM0051 v1.0 equations
- Quadrature error propagation discount
- 10% non-permanence buffer pool deduction
- 1.5056 tCO2e net creditable volume @ ₹1,200/t = 180,672 paise (₹1,806.72)
- Largest Remainder Method: Farmer ₹1,264.70 (70%), Co-op ₹271.01 (15%), Platform ₹271.01 (15%)
- Exact sum match (zero rounding leak)
"""

import pytest
from services.api.mrv.vm0051 import calculate_vm0051_reductions, VM0051Input, VM0051_CONFIG
from services.api.payments.money import calculate_gross_paise, allocate_benefit_sharing, format_inr

def test_golden_mrv_end_to_end_calculation():
    # Input: 1.08 ha, 105 days
    mrv_input = VM0051Input(
        plot_area_ha=1.08,
        cultivation_duration_days=105,
        baseline_water_regime="CONTINUOUS_FLOODING",
        project_water_regime="SAFE_AWD",
        region="telangana_andhra"
    )

    res = calculate_vm0051_reductions(mrv_input)

    # 1. Emission Assertions
    # Baseline CH4: 1.30 * 105 * 1.08 = 147.42 kg CH4
    assert res.baseline_ch4_kg == pytest.approx(147.42, 0.01)
    # Project CH4: 1.30 * 0.52 * 105 * 1.08 = 76.6584 kg CH4
    assert res.project_ch4_kg == pytest.approx(76.6584, 0.01)
    # Baseline tCO2e: 147.42 / 1000 * 28 = 4.1278 tCO2e
    assert res.baseline_emissions_tco2e == pytest.approx(4.1278, 0.001)
    # Project tCO2e: 76.6584 / 1000 * 28 = 2.1464 tCO2e
    assert res.project_emissions_tco2e == pytest.approx(2.1464, 0.001)
    # Gross Reduction: 4.1278 - 2.1464 = 1.9814 tCO2e
    assert res.gross_reduction_tco2e == pytest.approx(1.9814, 0.001)

    # 2. Uncertainty & Buffer Deductions
    # Quadrature uncertainty = 25.57%
    assert res.uncertainty_relative_pct == pytest.approx(25.57, 0.1)
    # Deduction pct = 25.57% - 10.0% = 15.57%
    assert res.uncertainty_deduction_pct == pytest.approx(15.57, 0.1)
    # Uncertainty discount tCO2e = 0.3086 tCO2e
    assert res.uncertainty_discount_tco2e == pytest.approx(0.3086, 0.001)
    # 10% Buffer pool deduction: (1.9814 - 0.3086) * 0.10 = 0.1673 tCO2e
    assert res.buffer_pool_deduction_tco2e == pytest.approx(0.1673, 0.001)

    # Net Creditable Volume: 1.5055 ~ 1.5056 tCO2e
    assert res.net_creditable_tco2e_point == pytest.approx(1.5056, 0.001)

    # 3. Financial Conversion @ Contractual Floor Price ₹1,200/t
    price_per_tonne = 1200
    # Expected gross proceeds: 1.5056 * 120,000 paise = 180,672 paise (₹1,806.72)
    gross_paise = calculate_gross_paise(1.5056, price_per_tonne)
    assert gross_paise == 180672

    # 4. Hare-Niemeyer Largest Remainder Allocation
    split = allocate_benefit_sharing(gross_paise, formula_version="VM0051-BS-V1.0")

    # Invariant: Sum must exactly equal 180,672 paise (zero leak)
    assert (split.farmer_paise + split.cooperative_paise + split.platform_paise) == 180672

    # Exact expected shares
    assert split.farmer_paise == 126470      # 70% floor + remainder
    assert split.cooperative_paise == 27101  # 15% + 1 remainder paise
    assert split.platform_paise == 27101     # 15% + 1 remainder paise

    # Currency format verification
    assert format_inr(gross_paise) == "₹1,806.72"
    assert format_inr(split.farmer_paise) == "₹1,264.70"
    assert format_inr(split.cooperative_paise) == "₹271.01"
    assert format_inr(split.platform_paise) == "₹271.01"
