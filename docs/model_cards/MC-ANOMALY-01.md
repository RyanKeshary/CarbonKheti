# Model Card: MC-ANOMALY-01 (Explainable Anomaly & Fraud Scorer)

## Model Overview
- **Model Name:** Explainable Multi-Source Agricultural Anomaly Scorer
- **Identifier:** `MC-ANOMALY-01`
- **Version:** 1.0 (Rule-Based Expert System + Multivariate Covariance Outlier Detection)
- **Primary Task:** Detecting behavioral, perceptual, and spatial anomalies in farmer evidence submissions.
- **Maintainer:** CarbonKheti Risk & Verification Team

## Core Safety Policy (Section 8.2)
**THE SYSTEM NEVER AUTO-REJECTS A FARMER ON A MODEL SCORE ALONE.**
All anomaly flags are 100% explainable and must be audited by a human cooperative field officer or accredited VVB auditor before any adverse determination.

## Feature Architecture & Risk Weights
| Rule / Metric | Trigger Condition | Risk Weight | Rationale |
|---|---|---|---|
| **Perceptual Hash Collision** | Identical image dHash across different plots/farmers | $+40$ | Photo evidence reuse fraud |
| **Active Fire Detection** | NASA FIRMS hotspot inside plot during harvest | $+35$ | Post-harvest stubble burning violates VM0051 |
| **GPS Geofence Violation** | Photo EXIF coordinates $> 300\text{ m}$ from declared plot centroid | $+25$ | Evidence collected off-site |
| **Zero Variance Reading** | Std deviation of $\ge 5$ water tube readings $< 0.5\text{ cm}$ | $+20$ | Fabricated or copied field logs |
| **Insufficient Evidence** | Zero photos or $< 3$ seasonal water tube logs | $+20$ | Inadequate MRV auditable trail |
| **Multivariate Outlier** | Normalised distance norm $> 3.8$ standard deviations | $+15$ | Behavioral statistical outlier |

## Human Escalation Path
- Score $< 30$: Normal verification processing.
- Score $30 - 59$: Flagged for cooperative agent field verification visit.
- Score $\ge 60$: Flagged for senior auditor inspection before tranche disbursement.
