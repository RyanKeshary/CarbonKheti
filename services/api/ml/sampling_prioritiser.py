"""
Stratified Sampling Plan Generator & Audit Risk Prioritiser.
Section 8 & Section 10 Mandate:
- Seeded, deterministic pseudo-random stratified selection (5-10% rate)
- Stored seed and parameters for byte-for-byte audit reproducibility
- Explainable risk-scoring prioritisation for auditor field visits
"""

import random
from typing import List, Dict, Any

class SamplingEngine:
    @staticmethod
    def generate_stratified_sample(
        plots: List[Dict[str, Any]],
        sample_rate_pct: float = 10.0,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Stratifies plots by village/district and performs reproducible seeded sampling.
        """
        rng = random.Random(seed)
        
        # Group by stratum (e.g. village or district)
        strata: Dict[str, List[Dict[str, Any]]] = {}
        for p in plots:
            strat_key = p.get("village", p.get("district", "DEFAULT_STRATUM"))
            if strat_key not in strata:
                strata[strat_key] = []
            strata[strat_key].append(p)

        selected_plots: List[Dict[str, Any]] = []
        for strat_name, plot_list in strata.items():
            k = max(1, int(round(len(plot_list) * (sample_rate_pct / 100.0))))
            # Sort deterministically before sampling
            sorted_plots = sorted(plot_list, key=lambda x: str(x.get("id", "")))
            sampled = rng.sample(sorted_plots, min(k, len(sorted_plots)))
            selected_plots.extend(sampled)

        return {
            "seed": seed,
            "sample_rate_pct": sample_rate_pct,
            "total_plots_evaluated": len(plots),
            "sampled_count": len(selected_plots),
            "stratification_method": "VILLAGE_STRATIFIED",
            "sampled_plot_ids": [p.get("id") for p in selected_plots],
            "audit_reproducibility": "Exact seed matching verifies VVB independent replication"
        }

    @staticmethod
    def rank_plots_by_risk(plots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates an explainable verification priority score (0-100) based on:
        - Days since last tube reading (>5 days adds 30 pts)
        - SAR / tube reading discrepancy (adds 40 pts)
        - Irregular boundary complexity (adds 15 pts)
        - Fire detection flag (adds 50 pts)
        """
        ranked = []
        for p in plots:
            risk_score = 0.0
            reasons = []

            days_since = p.get("days_since_reading", 0)
            if days_since > 5:
                score_inc = min(35.0, days_since * 5.0)
                risk_score += score_inc
                reasons.append(f"Missing water-tube reading ({days_since} days elapsed)")

            if p.get("sar_tube_discrepancy", False):
                risk_score += 40.0
                reasons.append("Sentinel-1 radar backscatter contradicts tube reading")

            if p.get("fire_detected_near", False):
                risk_score += 50.0
                reasons.append("NASA FIRMS active thermal anomaly logged near boundary")

            if p.get("boundary_overlap_warning", False):
                risk_score += 30.0
                reasons.append("Geometry vertex proximity warning with adjacent parcel")

            risk_score = min(100.0, risk_score)
            ranked.append({
                "plot_id": p.get("id"),
                "farmer_name": p.get("farmer_name", "Farmer"),
                "area_ha": p.get("area_ha", 1.0),
                "risk_score": round(risk_score, 1),
                "risk_priority": "HIGH" if risk_score >= 60 else ("MEDIUM" if risk_score >= 30 else "LOW"),
                "reasons": reasons
            })

        return sorted(ranked, key=lambda x: x["risk_score"], reverse=True)
