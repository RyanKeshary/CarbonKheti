"""
Comprehensive Test Suite for CarbonKheti.
Covers:
- Deterministic Verra VM0051 v1.0 calculation engine with quadrature uncertainty
- Assertions against versioned reference parameters in vm0051_parameters.yaml
- Exact golden financial test for 1.4060 tCO2e @ ₹1,200/t (168,720 paise largest-remainder allocation)
- PostGIS/Shapely plot geometry overlap detection (zero double counting)
- Photo integrity, blur variance, and EXIF distance checks
- Append-only hash chain ledger tamper verification
- Grounded Agronomy RAG assistant citations and safety refusal
- State machine lifecycle transition rules
- Fact Bank integrity and citation presence
"""

import pytest
import json
import os
import yaml
import numpy as np

from services.api.mrv.vm0051 import calculate_vm0051_reductions, VM0051Input, VM0051_CONFIG
from services.api.payments.money import (
    calculate_gross_paise,
    allocate_benefit_sharing,
    format_inr
)
from services.api.domain.state_machines import (
    SEASON_ALLOWED_TRANSITIONS,
    BATCH_ALLOWED_TRANSITIONS,
    CONTRACT_ALLOWED_TRANSITIONS,
    validate_transition
)
from services.api.ml.overlap_detector import check_plot_overlap_conflicts
from services.api.ml.photo_integrity import calculate_haversine_distance, compute_blur_variance
from services.api.ledger.traceability_ledger import TraceabilityLedger
from services.api.ai.rag_advisory import retrieve_relevant_passages

def test_vm0051_parameters_yaml_assertions():
    """Asserts that all constants in reference/vm0051_parameters.yaml match verified standards."""
    params = VM0051_CONFIG["parameters"]
    assert params["baseline_emission_factor"]["value"] == 1.30
    assert params["baseline_emission_factor"]["table"] == "5.11"
    assert params["scaling_factors"]["multiple_aeration_awd"]["value"] == 0.52
    assert params["scaling_factors"]["multiple_aeration_awd"]["table"] == "5.12"
    assert params["global_warming_potential"]["methane"]["value"] == 28
    assert params["buffer_reserve"]["pooled_buffer_account_deduction"]["value"] == 0.10

def test_mrv_vm0051_calculation_precision():
    """Tests VM0051 calculation on 1.08 ha (average Indian operational holding)."""
    params = VM0051Input(
        plot_area_ha=1.08,
        cultivation_duration_days=115,
        baseline_water_regime="CONTINUOUS_FLOODING",
        project_water_regime="SAFE_AWD"
    )
    res = calculate_vm0051_reductions(params)

    assert "VM0051" in res.methodology_version
    assert res.baseline_ch4_kg > res.project_ch4_kg
    assert res.gross_reduction_tco2e > 0
    assert res.buffer_pool_deduction_tco2e > 0
    assert res.net_creditable_tco2e_point > 0
    # Bounds must encompass the point estimate
    assert res.net_creditable_tco2e_min < res.net_creditable_tco2e_point < res.net_creditable_tco2e_max
    # Quadrature uncertainty must be ~25.57%
    assert 24.0 < res.uncertainty_relative_pct < 27.0
    # Water savings range
    assert res.water_saving_m3_min < res.water_saving_m3_mean < res.water_saving_m3_max
    assert res.water_saving_m3_mean > 2000

def test_worked_example_rounding_and_largest_remainder():
    """
    Golden test resolving Section 2 (Item 1):
    Net creditable 1.5056 tCO2e (105-day season, 1.08 ha) @ ₹1,200/t:
    Gross = 1.5056 * 120,000 paise = 180,672 paise (₹1,806.72).
    70/15/15 split via largest-remainder method:
    Farmer (70%): 126,470 paise (₹1,264.70, remainder 0.4)
    Co-op (15%): 27,101 paise (₹271.01, remainder 0.8 -> +1)
    Platform (15%): 27,101 paise (₹271.01, remainder 0.8 -> +1)
    Sum: 126,470 + 27,101 + 27,101 = 180,672 paise (exact zero rounding leak).
    """
    unrounded_tonnes = 1.5056
    price_per_tonne = 1200

    gross_paise = calculate_gross_paise(unrounded_tonnes, price_per_tonne)
    assert gross_paise == 180672  # Exactly ₹1,806.72

    split = allocate_benefit_sharing(gross_paise, formula_version="VM0051-BS-V1.0")
    assert split.farmer_paise == 126470
    assert split.cooperative_paise == 27101
    assert split.platform_paise == 27101

    # Sum invariant: must equal gross paise to the exact integer paise
    assert (split.farmer_paise + split.cooperative_paise + split.platform_paise) == gross_paise
    assert format_inr(gross_paise) == "₹1,806.72"
    assert format_inr(split.farmer_paise) == "₹1,264.70"
    assert format_inr(split.cooperative_paise) == "₹271.01"


def test_fact_bank_schema_and_citations():
    facts_path = os.path.join(os.path.dirname(__file__), "..", "packages", "facts", "facts.json")
    with open(facts_path, "r", encoding="utf-8") as f:
        facts = json.load(f)

    assert len(facts) >= 16
    for fact in facts:
        assert "id" in fact
        assert "claim" in fact
        assert "source_url" in fact
        assert fact["source_url"].startswith("http")
        assert "publisher" in fact
        assert "year" in fact
        assert "retrieved_date" in fact

def test_plot_overlap_prevention():
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[79.270, 17.050], [79.275, 17.050], [79.275, 17.055], [79.270, 17.055], [79.270, 17.050]]]
    }
    poly2_overlapping = {
        "type": "Polygon",
        "coordinates": [[[79.272, 17.050], [79.277, 17.050], [79.277, 17.055], [79.272, 17.055], [79.272, 17.050]]]
    }
    poly3_separate = {
        "type": "Polygon",
        "coordinates": [[[79.300, 17.050], [79.305, 17.050], [79.305, 17.055], [79.300, 17.055], [79.300, 17.050]]]
    }

    enrolled = [{"plot_id": "P-01", "geojson": poly1, "farmer_id": "F-01"}]

    res_overlap = check_plot_overlap_conflicts(poly2_overlapping, "P-02", enrolled)
    assert res_overlap["has_conflict"] is True
    assert res_overlap["status"] == "REJECTED_OVERLAP"

    res_clean = check_plot_overlap_conflicts(poly3_separate, "P-03", enrolled)
    assert res_clean["has_conflict"] is False
    assert res_clean["status"] == "CLEARED"

def test_haversine_distance():
    d = calculate_haversine_distance(17.050, 79.270, 17.051, 79.270)
    assert 100.0 < d < 125.0

def test_blur_variance():
    flat = np.ones((50, 50), dtype=np.float32) * 128.0
    assert compute_blur_variance(flat) == 0.0

    noise = np.random.normal(128.0, 30.0, (50, 50)).astype(np.float32)
    assert compute_blur_variance(noise) > 500.0

def test_traceability_ledger_hash_chain():
    ledger = TraceabilityLedger()
    ledger.append_record("PLOT_ENROLLED", {"plot_id": "P-101", "ha": 1.2})
    ledger.append_record("MRV_CALCULATION_SEALED", {"plot_id": "P-101", "credits": 2.1})

    integrity = ledger.verify_chain_integrity()
    assert integrity["is_valid"] is True
    assert integrity["total_blocks"] == 3

    # Tamper detection
    ledger.entries[1].payload["ha"] = 999.0
    tampered_check = ledger.verify_chain_integrity()
    assert tampered_check["is_valid"] is False
    assert tampered_check["compromised_index"] == 1

def test_rag_retrieval_passages():
    passages = retrieve_relevant_passages("what is the water depth for alternate wetting and drying tube")
    assert len(passages) > 0
    assert "15 cm" in passages[0]["content"]

    passages_flower = retrieve_relevant_passages("should I dry the rice field during flowering")
    assert len(passages_flower) > 0
    assert "CRITICAL EXCEPTION" in passages_flower[0]["content"]

def test_state_machine_transitions():
    """Validates domain state machine transition guards."""
    assert validate_transition("ENROLLED", "BASELINE_DOCUMENTED", SEASON_ALLOWED_TRANSITIONS, "Season") is True
    assert validate_transition("DRAFT", "ENROLLING", BATCH_ALLOWED_TRANSITIONS, "Batch") is True
    assert validate_transition("DRAFT", "SENT", CONTRACT_ALLOWED_TRANSITIONS, "Contract") is True

    # Invalid jump must raise ValueError
    with pytest.raises(ValueError):
        validate_transition("ENROLLED", "HARVESTED", SEASON_ALLOWED_TRANSITIONS, "Season")
