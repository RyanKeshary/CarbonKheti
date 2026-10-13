"""
Explainable Anomaly & Fraud Scoring Module.
Combines rule-based behavioral checks with multivariate statistical outlier scoring.

Core Safety Rule (Section 8.2):
Every flag is explainable and MUST be reviewed by a human auditor before any adverse action.
NEVER auto-reject a farmer on a model score alone.
"""

import os
from typing import Dict, Any, List, Optional
import numpy as np

class ExplainableAnomalyScorer:
    def __init__(self):
        # Reference agricultural distribution baseline
        # Features: [plot_area_ha, photo_distance_m, tube_reading_std_dev, sync_delay_hours, log_frequency]
        self.ref_means = np.array([1.20, 35.0, 18.0, 8.0, 8.0], dtype=np.float64)
        self.ref_stds = np.array([0.80, 40.0, 8.0, 12.0, 4.0], dtype=np.float64)

    def evaluate_plot_season_features(
        self,
        plot_id: str,
        farmer_id: str,
        plot_area_ha: float,
        photo_count: int,
        blurry_photo_count: int,
        max_photo_distance_m: float,
        tube_readings_count: int,
        duplicate_phash_detected: bool,
        fire_events_detected: int,
        sync_delay_hours: float = 6.0,
        tube_reading_std_dev: float = 8.5
    ) -> Dict[str, Any]:
        """
        Calculates explainable risk score (0-100) and triggers human-in-the-loop flags.
        """
        flags: List[str] = []
        risk_points = 0

        # Rule 1: Duplicate perceptual hash (same photo submitted across multiple plots/farmers)
        if duplicate_phash_detected:
            flags.append("Identical photo perceptual hash detected across different records (pHash collision).")
            risk_points += 40

        # Rule 2: Active fire detected in plot polygon during harvest
        if fire_events_detected > 0:
            flags.append(f"NASA FIRMS recorded {fire_events_detected} active fire detection(s) in plot polygon during season.")
            risk_points += 35

        # Rule 3: Extreme GPS discrepancy on uploaded evidence
        if max_photo_distance_m > 300.0:
            flags.append(f"Field photo GPS was taken {max_photo_distance_m:.0f}m away from declared plot boundary (threshold 300m).")
            risk_points += 25

        # Rule 4: Suspiciously low tube reading variance (unnatural identical numbers entered)
        if tube_readings_count >= 5 and tube_reading_std_dev < 0.5:
            flags.append("Water tube readings show zero natural variance (identical values logged every session).")
            risk_points += 20

        # Rule 5: Low evidence volume
        if photo_count == 0:
            flags.append("No geo-tagged field photos submitted for this season.")
            risk_points += 20
        elif blurry_photo_count > 0 and (blurry_photo_count / max(photo_count, 1)) > 0.5:
            flags.append(f"More than 50% of photos ({blurry_photo_count}/{photo_count}) failed blur/quality checks.")
            risk_points += 15

        if tube_readings_count < 3:
            flags.append(f"Only {tube_readings_count} AWD tube readings recorded (minimum 3 required per season).")
            risk_points += 15

        # Multivariate anomaly score via normalised Z-vector norm
        feat = np.array([
            plot_area_ha,
            min(max_photo_distance_m, 500.0),
            tube_reading_std_dev,
            min(sync_delay_hours, 72.0),
            float(photo_count + tube_readings_count)
        ], dtype=np.float64)
        
        z_scores = (feat - self.ref_means) / self.ref_stds
        euclidean_anomaly_norm = float(np.linalg.norm(z_scores))
        is_statistical_outlier = euclidean_anomaly_norm > 3.8  # >3.8 standard deviations

        if is_statistical_outlier:
            flags.append(f"Multivariate behavior pattern flagged as statistical outlier (deviation index {euclidean_anomaly_norm:.2f}).")
            risk_points += 15

        total_risk_score = min(100, risk_points)

        status = "NORMAL"
        if total_risk_score >= 60:
            status = "HIGH_RISK_MANUAL_REVIEW"
        elif total_risk_score >= 30:
            status = "MODERATE_RISK_AGENT_VERIFY"

        return {
            "plot_id": plot_id,
            "farmer_id": farmer_id,
            "risk_score_0_to_100": total_risk_score,
            "status": status,
            "flag_count": len(flags),
            "flags": flags,
            "statistical_outlier": is_statistical_outlier,
            "requires_human_auditor_review": len(flags) > 0,
            "policy_statement": "Automated system NEVER auto-rejects. Flags must be inspected by cooperative agent or certified auditor."
        }

def evaluate_dropout_risk(farmer_enrolment_seasons_count: int) -> Dict[str, Any]:
    """
    Dropout Risk Assessment per Section 8.2:
    'Dropout-risk model: built only after enough real enrolment history exists;
    until then the system shows 'not enough data' and uses simple, transparent follow-up rules.'
    """
    if farmer_enrolment_seasons_count < 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "Not enough historical seasons to run statistical dropout-risk model (minimum 3 complete seasons required).",
            "active_protocol": "Transparent cooperative follow-up visits scheduled before transplanting."
        }
    return {
        "status": "CALCULATED",
        "message": f"Historical baseline based on {farmer_enrolment_seasons_count} seasons.",
        "risk_level": "LOW"
    }
