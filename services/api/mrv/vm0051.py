"""
Verra VM0051 (Improved Management in Rice Production Systems, v1.0)
Deterministic MRV Emission Reduction Calculation Engine.

Implements:
- Verra VM0051 v1.0 & IPCC 2019 Refinement (Vol. 4, Ch. 5, Tables 5.11/5.12)
- Parameters loaded from versioned reference file: services/api/reference/vm0051_parameters.yaml
- Sourced Quadrature Error Propagation (U_total = sqrt(sum(U_i^2)))
- Separate 10% Pooled Buffer deduction from credit volume
- Sourced Regional Water Savings Range (IWMI/IRRI & CGWB)
"""

import os
import yaml
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, Optional

# Load versioned parameters from YAML reference
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARAM_FILE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "reference", "vm0051_parameters.yaml"))

def load_vm0051_parameters() -> Dict[str, Any]:
    if os.path.exists(PARAM_FILE_PATH):
        with open(PARAM_FILE_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

VM0051_CONFIG = load_vm0051_parameters()

# Extract parameters with fallback to verified IPCC 2019 Refinement defaults
PARAMS = VM0051_CONFIG.get("parameters", {})
DEFAULT_EF_C_KG_PER_HA_DAY = PARAMS.get("baseline_emission_factor", {}).get("value", 1.30)
SF_W_CONTINUOUS_FLOODING = PARAMS.get("scaling_factors", {}).get("continuous_flooding", {}).get("value", 1.00)
SF_W_SAFE_AWD = PARAMS.get("scaling_factors", {}).get("multiple_aeration_awd", {}).get("value", 0.52)
SF_P_DEFAULT = PARAMS.get("scaling_factors", {}).get("pre_season_non_flooded", {}).get("value", 1.00)
SF_O_DEFAULT = PARAMS.get("scaling_factors", {}).get("organic_amendments_none", {}).get("value", 1.00)
GWP_CH4_AR5 = float(PARAMS.get("global_warming_potential", {}).get("methane", {}).get("value", 28.0))
DEFAULT_BUFFER_POOL_PCT = float(PARAMS.get("buffer_reserve", {}).get("pooled_buffer_account_deduction", {}).get("percentage", 10.0))

# Relative uncertainties for quadrature
UNCERT_CONFIG = PARAMS.get("uncertainty_propagation", {}).get("parameter_uncertainties", {})
U_EF = UNCERT_CONFIG.get("emission_factor", 0.20)
U_SF_W = UNCERT_CONFIG.get("scaling_factor_awd", 0.15)
U_AREA = UNCERT_CONFIG.get("plot_polygon_area", 0.05)
U_DAYS = UNCERT_CONFIG.get("cultivation_days", 0.02)

@dataclass(frozen=True)
class VM0051Input:
    plot_area_ha: float
    cultivation_duration_days: int
    baseline_water_regime: str = "CONTINUOUS_FLOODING"
    project_water_regime: str = "SAFE_AWD"
    region: str = "telangana_andhra"
    ef_c: float = DEFAULT_EF_C_KG_PER_HA_DAY
    sf_p: float = SF_P_DEFAULT
    sf_o: float = SF_O_DEFAULT
    buffer_pool_rate_pct: float = DEFAULT_BUFFER_POOL_PCT
    gwp_ch4: float = GWP_CH4_AR5

@dataclass
class VM0051Result:
    methodology_version: str
    parameter_spec_version: str
    citation: str
    plot_area_ha: float
    cultivation_duration_days: int
    baseline_ch4_kg: float
    project_ch4_kg: float
    ch4_reduction_kg: float
    baseline_emissions_tco2e: float
    project_emissions_tco2e: float
    gross_reduction_tco2e: float
    leakage_tco2e: float
    uncertainty_method: str
    uncertainty_relative_pct: float
    uncertainty_deduction_pct: float
    uncertainty_discount_tco2e: float
    buffer_pool_deduction_tco2e: float
    net_creditable_tco2e_point: float
    net_creditable_tco2e_min: float
    net_creditable_tco2e_max: float
    confidence_interval_95_pct: float
    water_saving_m3_min: float
    water_saving_m3_max: float
    water_saving_m3_mean: float
    step_by_step_audit: Dict[str, Any]

def calculate_vm0051_reductions(params: VM0051Input) -> VM0051Result:
    """
    Executes Deterministic Verra VM0051 v1.0 Algorithm:
    1. Daily emission rate: EF_i = EF_c * SF_w * SF_p * SF_o
    2. Seasonal CH4 emissions: E_season = EF_i * days * area_ha (in kg CH4)
    3. Conversion to tCO2e: (kg CH4 / 1000) * GWP_CH4 (AR5 GWP = 28)
    4. Gross Reduction: BE - PE - Leakage
    5. Uncertainty discount via Quadrature Error Propagation:
       U_total = sqrt(U_EF^2 + U_SFw^2 + U_area^2 + U_days^2)
    6. Non-permanence Buffer Pool Reserve: 10% deduction into Pooled Buffer Account
    7. Net Creditable tCO2e = Gross - Uncertainty Discount - Buffer Pool
    """
    if params.plot_area_ha <= 0:
        raise ValueError("Plot area must be strictly positive")
    if params.cultivation_duration_days <= 0:
        raise ValueError("Cultivation duration must be strictly positive")

    # Baseline daily emission factor (kg CH4 / ha / day)
    ef_base = params.ef_c * SF_W_CONTINUOUS_FLOODING * params.sf_p * params.sf_o
    # Project daily emission factor
    sf_w_proj = SF_W_SAFE_AWD if params.project_water_regime == "SAFE_AWD" else SF_W_CONTINUOUS_FLOODING
    ef_proj = params.ef_c * sf_w_proj * params.sf_p * params.sf_o

    # Total seasonal CH4 emissions (kg CH4)
    baseline_ch4_kg = ef_base * params.cultivation_duration_days * params.plot_area_ha
    project_ch4_kg = ef_proj * params.cultivation_duration_days * params.plot_area_ha
    ch4_reduction_kg = baseline_ch4_kg - project_ch4_kg

    # Convert to tCO2e using AR5 GWP (28)
    baseline_tco2e = (baseline_ch4_kg / 1000.0) * params.gwp_ch4
    project_tco2e = (project_ch4_kg / 1000.0) * params.gwp_ch4
    gross_reduction_tco2e = baseline_tco2e - project_tco2e

    # Leakage is 0.0 for in-situ water regime management without displacement
    leakage_tco2e = 0.0

    # Quadrature Error Propagation:
    # U_total = sqrt(U_EF^2 + U_SF_W^2 + U_AREA^2 + U_DAYS^2)
    combined_uncert_pct = math.sqrt(
        (U_EF ** 2) + (U_SF_W ** 2) + (U_AREA ** 2) + (U_DAYS ** 2)
    ) * 100.0  # Approx 25.57%

    # VM0051 / CDM Tool 03 Threshold Discount Rule:
    # If combined half-width uncertainty at 95% exceeds 10%, deduct (U_total - 10%)
    if combined_uncert_pct > 10.0:
        uncertainty_deduction_pct = round(combined_uncert_pct - 10.0, 4)
    else:
        uncertainty_deduction_pct = 0.0

    uncertainty_discount_tco2e = gross_reduction_tco2e * (uncertainty_deduction_pct / 100.0)

    # 10% Buffer pool deduction from credit volume into Verra Pooled Buffer Account
    buffer_pool_tco2e = (gross_reduction_tco2e - uncertainty_discount_tco2e) * (params.buffer_pool_rate_pct / 100.0)

    # Net Creditable Reductions
    net_creditable_point = max(0.0, gross_reduction_tco2e - uncertainty_discount_tco2e - buffer_pool_tco2e)

    # 95% Confidence Interval bounds (using quadrature relative uncertainty)
    uncert_fraction = combined_uncert_pct / 100.0
    net_creditable_min = max(0.0, net_creditable_point * (1.0 - uncert_fraction))
    net_creditable_max = net_creditable_point * (1.0 + uncert_fraction)

    # Water savings range by agro-climatic region (IWMI / IRRI & CGWB data)
    water_params = PARAMS.get("water_saving_baseline", {}).get("baseline_consumption_m3_per_ha", {})
    region_key = params.region if params.region in water_params else "telangana_andhra"
    base_water = water_params.get(region_key, {"min": 9500, "max": 12000})
    
    # AWD water conservation is 15% to 30% (mean 22.5%)
    water_saving_min = params.plot_area_ha * base_water["min"] * 0.15
    water_saving_max = params.plot_area_ha * base_water["max"] * 0.30
    water_saving_mean = params.plot_area_ha * ((base_water["min"] + base_water["max"]) / 2.0) * 0.225

    step_audit = {
        "formula": "ER_net = (BE - PE - Leakage - Uncertainty_Discount) * (1 - Buffer_Rate)",
        "equations": {
            "BE_tco2e": f"({params.ef_c} * 1.0 * {params.cultivation_duration_days} * {params.plot_area_ha} / 1000) * {params.gwp_ch4} = {baseline_tco2e:.4f}",
            "PE_tco2e": f"({params.ef_c} * {sf_w_proj} * {params.cultivation_duration_days} * {params.plot_area_ha} / 1000) * {params.gwp_ch4} = {project_tco2e:.4f}",
            "Gross_ER": f"{baseline_tco2e:.4f} - {project_tco2e:.4f} = {gross_reduction_tco2e:.4f}",
            "Quadrature_Uncertainty": f"sqrt({U_EF}^2 + {U_SF_W}^2 + {U_AREA}^2 + {U_DAYS}^2) = {combined_uncert_pct:.2f}%",
            "Uncertainty_Deduction": f"max(0, {combined_uncert_pct:.2f}% - 10%) = {uncertainty_deduction_pct:.2f}% -> {uncertainty_discount_tco2e:.4f} tCO2e",
            "Verra_Buffer_Reserve_10pct": f"{params.buffer_pool_rate_pct}% -> {buffer_pool_tco2e:.4f} tCO2e withheld into Pooled Account",
            "Net_Creditable": f"{net_creditable_point:.4f} tCO2e (95% CI: [{net_creditable_min:.4f}, {net_creditable_max:.4f}])",
            "Water_Saving_Range": f"[{water_saving_min:.0f}, {water_saving_max:.0f}] m3 (mean: {water_saving_mean:.0f} m3)"
        },
        "sources": {
            "baseline_ef": "IPCC 2019 Refinement, Vol 4, Ch 5, Table 5.11 (1.30 kg CH4/ha/day)",
            "sf_w_awd": "IPCC 2019 Refinement, Vol 4, Ch 5, Table 5.12 (0.52 scaling factor)",
            "gwp_ch4": "IPCC AR5 Table 8.7 (28 tCO2e/tCH4)",
            "buffer_pool": "Verra VCS Standard v4.5 Section 3.1.2 (10% non-permanence buffer)",
            "water_baseline": "IWMI/IRRI (2022) & CGWB Ground Water Yearbook"
        }
    }

    return VM0051Result(
        methodology_version="Verra VM0051 v1.0",
        parameter_spec_version=VM0051_CONFIG.get("version", "VM0051-PAR-2026-V1"),
        citation="Verra VM0051 v1.0 & IPCC 2019 Refinement Vol. 4, Ch. 5",
        plot_area_ha=params.plot_area_ha,
        cultivation_duration_days=params.cultivation_duration_days,
        baseline_ch4_kg=round(baseline_ch4_kg, 4),
        project_ch4_kg=round(project_ch4_kg, 4),
        ch4_reduction_kg=round(ch4_reduction_kg, 4),
        baseline_emissions_tco2e=round(baseline_tco2e, 4),
        project_emissions_tco2e=round(project_tco2e, 4),
        gross_reduction_tco2e=round(gross_reduction_tco2e, 4),
        leakage_tco2e=0.0,
        uncertainty_method="Quadrature Error Propagation (Gaussian 95% CI)",
        uncertainty_relative_pct=round(combined_uncert_pct, 2),
        uncertainty_deduction_pct=round(uncertainty_deduction_pct, 2),
        uncertainty_discount_tco2e=round(uncertainty_discount_tco2e, 4),
        buffer_pool_deduction_tco2e=round(buffer_pool_tco2e, 4),
        net_creditable_tco2e_point=round(net_creditable_point, 4),
        net_creditable_tco2e_min=round(net_creditable_min, 4),
        net_creditable_tco2e_max=round(net_creditable_max, 4),
        confidence_interval_95_pct=round(combined_uncert_pct, 2),
        water_saving_m3_min=round(water_saving_min, 1),
        water_saving_m3_max=round(water_saving_max, 1),
        water_saving_m3_mean=round(water_saving_mean, 1),
        step_by_step_audit=step_audit
    )
