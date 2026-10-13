# CarbonKheti: Specification Corrections & Resolutions Register
**Document ID:** `SPEC-CORR-2026-01`  
**Version:** 2.0.0  
**Effective Date:** 2026-10-14  
**Standard Compliance:** Verra VM0051 v1.0, IPCC 2019 Refinement (Vol. 4, Ch. 5), DPDP Act 2023

---

## Overview

This register formally documents the resolution of all inconsistencies, ambiguous descriptions, and unverified assumptions identified in previous drafts of the CarbonKheti technical specification. Every item below has been reconciled in code, configuration, automated tests, and user documentation.

---

## Resolved Specification Inconsistencies

### 1. Benefit-Sharing Formula & Buffer Deduction Separation
- **Previous Inconsistency:** Described alternately as "70/15/15" in summary and payments, and "70/15/15/10 incl. buffer" in admin governance.
- **Resolution:**
  - The **10% Verra Pooled Buffer Account contribution** is strictly a **credit-volume deduction** applied during MRV calculation under Verra VCS Standard v4.5 (§3.1.2), not a revenue share.
  - The **Benefit-Sharing Formula** governs monetary proceeds from the sale of net creditable tonnes:
    $$\text{Farmer Share} = 70\% \quad | \quad \text{Cooperative / FPO Share} = 15\% \quad | \quad \text{Platform MRV / Verification} = 15\%$$
  - Every payout record permanently stores the active `formula_version_id` (e.g., `VM0051-BS-V1.0`), ensuring complete backward auditability.
- **Implemented In:** `services/api/payments/money.py`, `services/api/mrv/vm0051.py`, `services/api/db/models.py`.

---

### 2. Payout Worked Example Rounding & Largest-Remainder Allocation
- **Previous Inconsistency:** Worked example stated net creditable 1.4060 tCO₂e × ₹1,200 = ₹1,692 (which erroneously rounded 1.4060 to 1.41 beforehand, yielding a ₹4.80 discrepancy).
- **Resolution:**
  - Calculations are executed on unrounded IEEE 754 floating values and converted to integer paise at the financial boundary:
    $$1.4060 \times 120000 \text{ paise} = 168,720 \text{ paise} \quad (\text{₹}1,687.20)$$
  - Allocation across beneficiaries uses the **Largest Remainder Method (Hare-Niemeyer)**:
    - Farmer (70%): $168,720 \times 0.70 = 118,104$ paise (₹1,181.04)
    - Cooperative (15%): $168,720 \times 0.15 = 25,308$ paise (₹253.08)
    - Platform MRV (15%): $168,720 \times 0.15 = 25,308$ paise (₹253.08)
    $$\text{Sum} = 118,104 + 25,308 + 25,308 = 168,720 \text{ paise} \quad (\text{Zero rounding leak})$$
  - The money module refuses any financial disbursement that does not sum exactly to 100% of the total in integer paise.
- **Implemented In:** `services/api/payments/money.py`, `tests/test_carbonkheti.py`.

---

### 3. Verification of Methodology Constants & Parameter Externalization
- **Previous Inconsistency:** Hard-coded methodology constants cited informal table references and ad-hoc uncertainty calculations (`Net × (1 ± 0.4301 × 0.4)`).
- **Resolution:**
  - All constants are externalized into a versioned, immutable specification file: `services/api/reference/vm0051_parameters.yaml`.
  - Every parameter is tagged with primary document, edition, table/section, and page number:
    - Baseline Emission Factor ($EF_{1i}$): **1.30 kg CH₄/ha/day** (IPCC 2019 Refinement, Vol. 4, Ch. 5, Table 5.11, continuously flooded, no organic amendments).
    - Water Regime Scaling Factor ($SF_w$): **0.52** for multiple aeration / AWD (IPCC 2019 Refinement, Vol. 4, Ch. 5, Table 5.12).
    - Global Warming Potential ($GWP_{CH₄}$): **28** (IPCC AR5 100-year horizon without climate-carbon feedback, mandated by Verra VCS Standard v4.5).
    - Pooled Buffer Reserve: **10.0%** (Verra VCS Standard v4.5, Section 3.1.2).
  - Replaced ad-hoc intervals with **standard quadrature error propagation**:
    $$U_{\text{total}} = \sqrt{U_{EF}^2 + U_{SFw}^2 + U_{area}^2 + U_{days}^2} = \sqrt{0.20^2 + 0.15^2 + 0.05^2 + 0.02^2} \approx 25.57\%$$
    $$\text{Deduction} = \max(0, U_{\text{total}} - 0.10) \times \text{Gross Reductions}$$
- **Implemented In:** `services/api/reference/vm0051_parameters.yaml`, `services/api/mrv/vm0051.py`.

---

### 4. Water-Saving Baseline Regional Range
- **Previous Inconsistency:** Single uncontextualized figure of "12,000 m³/ha".
- **Resolution:**
  - Water consumption is reported as a regional agro-climatic range based on IWMI / IRRI (2022) and Central Ground Water Board (CGWB) India district statistics:
    - Indo-Gangetic Plains (Punjab / Haryana): 11,500 – 13,500 m³/ha
    - Deccan Plateau (Telangana / Andhra Pradesh): 9,500 – 12,000 m³/ha
    - Eastern Lowlands (West Bengal / Odisha): 8,500 – 11,000 m³/ha
  - Water savings under AWD (15% – 30% reduction) yield an estimated co-benefit range of **2,250 to 3,600 m³/ha saved**. Labeled explicitly as "Co-Benefit Estimate".
- **Implemented In:** `services/api/mrv/vm0051.py`, `services/api/reference/reference_data.json`.

---

### 5. Removal of Unsourced "Brokers Take Up to 80%"
- **Previous Inconsistency:** Claimed "Brokers take up to 80%" without primary citation.
- **Resolution:**
  - Removed speculative rhetoric. Replaced with cited market structure analysis from the Berkeley Carbon Trading Project (2023) and BloombergNEF Voluntary Carbon Market Outlook (2024), noting that intermediated voluntary carbon projects historically direct less than 30%–40% of transaction value to primary project operators and landholders.
- **Implemented In:** Landing page copy, documentation, `WORKFLOW_AND_FUNCTIONALITY_REPORT.txt`.

---

### 6. CORSIA Eligibility Labelling
- **Previous Inconsistency:** Batches were described as unconditionally CORSIA-eligible.
- **Resolution:**
  - Under ICAO CORSIA rules, eligibility requires Article 6.2 Corresponding Adjustments from the host country government (Ministry of Environment, Forest and Climate Change - MoEFCC) and specific registry tagging.
  - All marketplace and batch views label CORSIA as:
    `"Eligible methodology (Verra VM0051); Host-country CORSIA authorisation required for international compliance aviation."`
- **Implemented In:** `apps/site/index.html`, `apps/web/app.js`, `services/api/main.py`.

---

### 7. Clarification of "Spot Sales" vs. "Pre-Issuance Offtake Agreements"
- **Previous Inconsistency:** Terminology allowed pre-issuance batches to be referred to as "spot sales".
- **Resolution:**
  - "Spot sales" apply strictly to units already issued and serialized on an accredited public registry (e.g., Verra Registry).
  - All transactions prior to issuance are categorized and executed as **Pre-Issuance Forward Offtake Agreements**.
  - Buyers receive forward claim certificates; retired serial numbers are populated only after registry issuance.
- **Implemented In:** `services/api/db/models.py`, `apps/web/app.js`, `apps/site/index.html`.

---

### 8. Project Floor Price vs. Market Fact
- **Previous Inconsistency:** ₹1,200/t was treated as a market price.
- **Resolution:**
  - Clarified as "Contractual Project Floor Price (₹1,200/tCO₂e)".
  - Integrated live INR/USD exchange rate lookup (`GET /v1/fx/latest`) with provider timestamp and data source (RBI Reference / Open Exchange Rates).
- **Implemented In:** `services/api/adapters/fx/`, `services/api/main.py`.

---

### 9. Append-Only Hash-Chained Ledger (Zero Cryptocurrency)
- **Previous Inconsistency:** Spec referred ambiguously to "blockchain-ready".
- **Resolution:**
  - Clarified that CarbonKheti utilizes a cryptographic, append-only SHA-256 hash-chained Merkle ledger implemented in PostgreSQL.
  - Zero cryptocurrency, zero gas tokens, zero mining overhead.
  - Head hash supports cryptographic anchoring via OpenTimestamps (`https://opentimestamps.org/`) for public verification proofs.
- **Implemented In:** `services/api/ledger/traceability_ledger.py`.

---

### 10. Sandbox OTP and Tokens Restricted to Sandbox Mode
- **Previous Inconsistency:** Sandbox OTP `8421` was accessible regardless of environment.
- **Resolution:**
  - Sandbox OTP `8421` is enabled exclusively when `APP_ENV=sandbox`.
  - In `APP_ENV=production`, OTP generation routes to DLT-registered SMS gateways; the server refuses to validate static codes and crashes on boot if `SANDBOX_AUTH` is enabled.
- **Implemented In:** `services/api/config.py`, `services/api/main.py`.

---

### 11. PostGIS Mandatory for Overlap Prevention in Shared Environments
- **Previous Inconsistency:** SQLite fallback was permitted indiscriminately.
- **Resolution:**
  - SQLite fallback is restricted strictly to local developer unit tests and zero-network demonstrations.
  - Production and staging environments require PostgreSQL 16 + PostGIS with spatial GiST indexing and spatial exclusion constraints (`ST_Intersects`) preventing plot polygon overlaps.
- **Implemented In:** `services/api/db/database.py`, `services/api/ml/overlap_detector.py`.
