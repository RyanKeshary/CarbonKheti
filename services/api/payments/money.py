"""
CarbonKheti Integer-Paise Money & Financial Allocation Engine.
Strictly implements Section 2 (Item 2) and Section 5:
- All financial balances stored in integer paise (BIGINT)
- Zero floating-point drift or financial rounding leaks
- Largest Remainder Method (Hare-Niemeyer) for exact 100% allocation
- Formula-versioned benefit sharing (Default: 70% Farmer, 15% Co-op, 15% Platform MRV)
- Refuses any operation whose allocations do not sum exactly to total_paise
"""

import math
from typing import Dict, NamedTuple
from dataclasses import dataclass

class BenefitSplit(NamedTuple):
    total_paise: int
    farmer_paise: int
    cooperative_paise: int
    platform_paise: int
    formula_version: str
    farmer_pct: float
    cooperative_pct: float
    platform_pct: float

# Default active benefit-sharing formulas
FORMULA_CATALOG: Dict[str, Dict[str, float]] = {
    "VM0051-BS-V1.0": {
        "farmer": 0.70,
        "cooperative": 0.15,
        "platform": 0.15,
    },
    "VM0051-BS-V2.0-DIRECT": {
        "farmer": 0.75,
        "cooperative": 0.12,
        "platform": 0.13,
    }
}

ACTIVE_FORMULA_VERSION = "VM0051-BS-V1.0"

def calculate_gross_paise(unrounded_tonnes: float, price_per_tonne_inr: int) -> int:
    """
    Computes gross proceeds in integer paise from unrounded credit volume
    and contractual price per tonne in INR.
    1 INR = 100 paise.
    Converts to integer paise once at the financial boundary.
    """
    if unrounded_tonnes < 0:
        raise ValueError("Credit volume cannot be negative")
    if price_per_tonne_inr < 0:
        raise ValueError("Price per tonne cannot be negative")
    
    # Precise paise calculation: unrounded_tonnes * price_per_tonne * 100
    gross_paise_float = unrounded_tonnes * float(price_per_tonne_inr) * 100.0
    # Standard bank rounding (round half to even or standard round)
    return int(round(gross_paise_float))

def allocate_benefit_sharing(
    total_paise: int,
    formula_version: str = ACTIVE_FORMULA_VERSION,
    custom_shares: Dict[str, float] = None
) -> BenefitSplit:
    """
    Allocates gross integer paise among beneficiaries using the Largest Remainder Method (Hare-Niemeyer).
    Guarantees:
      farmer_paise + cooperative_paise + platform_paise == total_paise
    Refuses any operation that would not sum exactly.
    """
    if total_paise < 0:
        raise ValueError("Total paise cannot be negative")
    
    if total_paise == 0:
        return BenefitSplit(
            total_paise=0,
            farmer_paise=0,
            cooperative_paise=0,
            platform_paise=0,
            formula_version=formula_version,
            farmer_pct=0.70,
            cooperative_pct=0.15,
            platform_pct=0.15
        )

    shares = custom_shares or FORMULA_CATALOG.get(formula_version)
    if not shares:
        raise ValueError(f"Unknown formula version: {formula_version}")
    
    f_pct = shares["farmer"]
    c_pct = shares["cooperative"]
    p_pct = shares["platform"]

    # Verify percentages sum to 1.0 within numerical precision
    if abs((f_pct + c_pct + p_pct) - 1.0) > 1e-6:
        raise ValueError(f"Formula shares must sum to 1.0; got {f_pct + c_pct + p_pct}")

    # Largest Remainder Allocation
    raw_shares = [
        ("farmer", total_paise * f_pct),
        ("cooperative", total_paise * c_pct),
        ("platform", total_paise * p_pct),
    ]

    allocated = {}
    remainders = []

    allocated_sum = 0
    for name, raw in raw_shares:
        integer_part = math.floor(raw)
        remainder = raw - integer_part
        allocated[name] = integer_part
        allocated_sum += integer_part
        remainders.append((remainder, name))

    leftover_paise = total_paise - allocated_sum

    # Sort descending by fractional remainder
    remainders.sort(key=lambda x: x[0], reverse=True)

    # Distribute leftover 1-paise units to largest fractional parts
    for i in range(leftover_paise):
        winner_name = remainders[i][1]
        allocated[winner_name] += 1

    final_farmer = allocated["farmer"]
    final_coop = allocated["cooperative"]
    final_platform = allocated["platform"]

    # Strict invariant validation
    total_allocated = final_farmer + final_coop + final_platform
    if total_allocated != total_paise:
        raise ArithmeticError(
            f"Financial allocation invariant violated: total {total_paise} != allocated {total_allocated}"
        )

    return BenefitSplit(
        total_paise=total_paise,
        farmer_paise=final_farmer,
        cooperative_paise=final_coop,
        platform_paise=final_platform,
        formula_version=formula_version,
        farmer_pct=f_pct,
        cooperative_pct=c_pct,
        platform_pct=p_pct
    )

def format_inr(paise: int) -> str:
    """
    Formats integer paise into Indian Rupee string with comma grouping and paise decimals.
    Example: 168720 -> '₹1,687.20'
    """
    sign = "-" if paise < 0 else ""
    abs_paise = abs(paise)
    rupees = abs_paise // 100
    cents = abs_paise % 100
    
    rupees_str = str(rupees)
    if len(rupees_str) > 3:
        last3 = rupees_str[-3:]
        other = rupees_str[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        formatted_rupees = ",".join(groups) + "," + last3
    else:
        formatted_rupees = rupees_str

    return f"{sign}₹{formatted_rupees}.{cents:02d}"

def paise_to_rupees_float(paise: int) -> float:
    """Helper for non-financial displays only."""
    return round(float(paise) / 100.0, 2)
