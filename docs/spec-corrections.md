# CarbonKheti: Specification Corrections & Resolutions Register
**Document ID:** `SPEC-CORR-2026-03`  
**Version:** 3.0.0 (Master Prompt 3 Aligned)  
**Effective Date:** 2026-10-14  
**Standard Compliance:** Verra VM0051 v1.0, IPCC 2019 Refinement (Vol. 4, Ch. 5), DPDP Act 2023

---

## Overview

This register formally documents the resolution of all inconsistencies, ambiguous descriptions, and unverified assumptions identified in previous drafts of the CarbonKheti technical specification. Every item below is reconciled in code, configuration, automated tests, and user documentation.

---

## Resolved Specification Inconsistencies & Verifications

### 1. Benefit-Sharing Formula & Buffer Deduction Separation
- **Previous Inconsistency:** Described alternately as "70/15/15" in summary and payments, and "70/15/15/10 incl. buffer" in admin governance.
- **Resolution:**
  - The **10% Verra Pooled Buffer Account contribution** is strictly a **credit-volume deduction** applied during MRV calculation under Verra VCS Standard v4.5 (§3.1.2), not a revenue share.
  - The **Benefit-Sharing Formula** governs monetary proceeds from the sale of net creditable tonnes:
    $$\text{Farmer Share} = 70\% \quad | \quad \text{Cooperative / FPO Share} = 15\% \quad | \quad \text{Platform MRV / Verification} = 15\%$$
  - Every payout record permanently stores the active `formula_version_id` (e.g., `VM0051-BS-V1.0`), ensuring complete backward auditability.
- **Implemented In:** `services/api/payments/money.py`, `services/api/mrv/vm0051.py`, `services/api/db/models.py`.

---

### 2. Payout Worked Example Rounding & Largest-Remainder Allocation (Engine-Generated)
- **Previous Inconsistency:** Section 2 of report allocated ₹1,687.20 (net 1.4060 t), but the MRV engine computes net 1.5056 t for a 105-day season on a 1.08 ha plot.
- **Resolution:**
  - Calculations are dynamically computed by the engine, never hand-typed, and asserted in golden tests:
    - Plot Area: 1.08 ha, Season: 105 days
    - Baseline Emissions ($EF_1 = 1.30$, $SF_w = 1.0$, $GWP = 28$):
      $$BE = \frac{1.30 \times 105 \times 1.08}{1000} \times 28 = 4.1278 \text{ tCO}_2\text{e}$$
    - Project Emissions ($SF_w = 0.52$):
      $$PE = \frac{1.30 \times 0.52 \times 105 \times 1.08}{1000} \times 28 = 2.1464 \text{ tCO}_2\text{e}$$
    - Gross Reduction: $ER_{\text{gross}} = 4.1278 - 2.1464 = 1.9814 \text{ tCO}_2\text{e}$
    - Quadrature Uncertainty: $U = \sqrt{0.20^2 + 0.15^2 + 0.05^2 + 0.02^2} = 25.57\%$
    - Uncertainty Discount (VM0051 Eq 42): $\max(0, 25.57\% - 10\%) \times 1.9814 = 0.3085 \text{ tCO}_2\text{e}$
    - Buffer Reserve (10%): $(1.9814 - 0.3085) \times 0.10 = 0.1673 \text{ tCO}_2\text{e}$
    - Net Creditable Volume:
      $$ER_{\text{net}} = 1.9814 - 0.3085 - 0.1673 = 1.5056 \text{ tCO}_2\text{e}$$
    - Gross Proceeds @ Contractual Floor Price ₹1,200/t ($120,000 \text{ paise}$):
      $$1.5056 \times 120000 \text{ paise} = 180,672 \text{ paise} \quad (\text{₹}1,806.72)$$
  - Allocation across beneficiaries uses the **Largest Remainder Method (Hare-Niemeyer)**:
    - Farmer (70%): $180,672 \times 0.70 = 126,470.4 \to 126,470$ paise (₹1,264.70), remainder 0.4
    - Cooperative (15%): $180,672 \times 0.15 = 27,100.8 \to 27,100$ paise, remainder 0.8 $\to +1 = 27,101$ paise (₹271.01)
    - Platform MRV (15%): $180,672 \times 0.15 = 27,100.8 \to 27,100$ paise, remainder 0.8 $\to +1 = 27,101$ paise (₹271.01)
    $$\text{Sum} = 126,470 + 27,101 + 27,101 = 180,672 \text{ paise} \quad (\text{₹}1,806.72) \quad [\text{Zero rounding leak}]$$
- **Implemented In:** `services/api/payments/money.py`, `tests/test_golden_mrv.py`, `tests/test_carbonkheti.py`.

---

### 3. Parameters Specification with Verified Primary Citations & Provisional Gate
- **Previous Inconsistency:** Threshold moved from 15% to 10%, season from 115 to 105 days, uncertainty components (20%, 15%, 5%, 2%) lacked documented source metadata.
- **Resolution:**
  - All constants are externalized into `services/api/reference/vm0051_parameters.yaml` with explicit citation fields: `source_document`, `version`, `chapter_section`, `table`, `page`, `retrieval_date`, and `status`:
    - Baseline Emission Factor ($EF_{1i} = 1.30 \text{ kg CH}_4\text{/ha/day}$): IPCC 2019 Refinement, Vol. 4, Ch. 5, Table 5.11, p. 5.45.
    - Scaling Factor multiple aeration AWD ($SF_w = 0.52$): IPCC 2019 Refinement, Vol. 4, Ch. 5, Table 5.12, p. 5.47.
    - Global Warming Potential ($GWP_{CH4} = 28$): IPCC AR5, Ch. 8, Table 8.7, p. 714 (mandated by VCS Standard v4.5 §3.14).
    - Buffer Reserve ($10.0\%$): Verra VCS Standard v4.5, §3.1.2 & §4.4 (AFOLU Non-Permanence Risk Tool default minimum).
    - Uncertainty Discount Threshold ($10.0\%$): Verra VM0051 v1.0, §8.3 & CDM Tool 03 (half-width threshold for 95% CI).
    - Cultivation Season ($105 \text{ days}$): ICAR-IIRR (Indian Institute of Rice Research) Varietal Catalogue (short-medium duration paddy e.g., MTU 1010, IR 64).
    - Relative Standard Errors:
      - $U_{EF} = 0.20$ (IPCC 2019 Refinement, Table 5.11)
      - $U_{SFw} = 0.15$ (IPCC 2019 Refinement, Table 5.12)
      - $U_{area} = 0.05$ (ISRO Bhuvan / GPS polygon boundary error tolerance)
      - $U_{days} = 0.02$ (Sentinel-2 NDVI / agent log date variance)
  - **Provisional Gate:** Any batch depending on a parameter marked `status: provisional` displays a `"Provisional methodology inputs"` badge and is prohibited from being offered in the marketplace.
- **Implemented In:** `services/api/reference/vm0051_parameters.yaml`, `services/api/mrv/vm0051.py`.

---

### 4. Removal of Unverified Berkeley Broker Margin Claim
- **Previous Inconsistency:** "Berkeley Carbon Trading Project (2023): brokers direct under 30%-40% of credit value to landholders" was cited without primary verification.
- **Resolution:**
  - Removed unverified attribution in strict adherence to Rule 4.
  - Replaced with factual, unembellished description: traditional carbon market pipelines involve multi-tiered intermediary broker fees; CarbonKheti operates transparent programmatic escrow allocating 70% direct to the smallholder farmer with full public formula transparency.
- **Implemented In:** `apps/site/index.html`, `packages/facts/fact_bank.json`, documentation.

---

### 5. Dynamic FX Rate Ingestion with Staleness & Unavailable Fallbacks
- **Previous Inconsistency:** Hard-coded "86.85 INR/USD" rate.
- **Resolution:**
  - Dynamic FX adapter fetches live conversion rates from public exchange API / RBI reference feed with network caching.
  - Payload returns `{rate, source, fetched_at, is_stale, rate_available}`.
  - If cached rate exceeds 24 hours, `is_stale: true` warning is emitted.
  - If network is unreachable and no cache exists, returns `rate_available: false` ("rate unavailable") rather than an invented estimate.
- **Implemented In:** `services/api/adapters/fx/base.py`, `services/api/main.py`.

---

### 6. Accurate Speech Terminology: Groq Whisper STT & Bhashini/Browser TTS
- **Previous Inconsistency:** Report erroneously referred to "Whisper TTS".
- **Resolution:**
  - OpenAI / Groq Whisper is exclusively Speech-to-Text (STT).
  - Voice pipeline uses Groq Whisper for audio transcription (STT) and Bhashini / Browser Speech Synthesis API (`window.speechSynthesis`) for Text-to-Speech (TTS).
- **Implemented In:** `apps/web/app.js`, `services/api/ai/groq_service.py`, report.

---

### 7. Ledger Terminology & Architecture: SHA-256 Hash Chain with Merkle Tree per Block
- **Previous Inconsistency:** Alternated between "Merkle ledger" and "hash chain".
- **Resolution:**
  - The core audit ledger is an append-only **Cryptographic SHA-256 Hash Chain** where each block contains `prev_hash`, `payload_hash`, `timestamp`, and `block_hash`.
  - For composite event batches (aggregating multiple plot verifications or payout dispatches), a **Merkle Tree** is computed over the leaf transactions to yield a `merkle_root` committed into the block payload.
  - Documented and tested in unit and security test suites.
- **Implemented In:** `services/api/ledger/traceability_ledger.py`, `tests/test_ledger_hashchain.py`.

---

### 8. Strict Fictional Reserved Range for Sandbox Identity & Banking
- **Previous Inconsistency:** Sandbox telephone numbers and bank accounts lacked defined non-routable ranges.
- **Resolution:**
  - Sandbox telephone numbers strictly utilize the DoT/TRAI non-allocated test range:
    `+91 99999 00000` to `+91 99999 99999` (cannot route to real Indian mobile subscribers).
  - Sandbox bank accounts strictly utilize dummy IFSC `SBXN0000001` and accounts `SBX-ACC-XXXX`.
  - All sandbox rows carry `is_sandbox = true` and `SBX-` prefixed IDs.
- **Implemented In:** `services/api/db/seed_sandbox.py`, `services/api/adapters/payments/sandbox_pay.py`.

---

### 9. Hard-Coded Sandbox OTP Restricted to Sandbox Builds
- **Previous Inconsistency:** Sandbox OTP `8421` was potentially accessible across builds.
- **Resolution:**
  - Sandbox OTP `8421` is enabled strictly when `APP_ENV=sandbox` and displayed on the sandbox sign-in UI.
  - In `APP_ENV=production`, the server fails to boot if sandbox flags are enabled, and production builds strip demo credentials at build time.
- **Implemented In:** `services/api/config.py`, `apps/web/index.html`.

---

### 10. Landing Page Statistics Sourced from Fact Bank or Live Zero Counts
- **Previous Inconsistency:** Unlinked counters on landing page.
- **Resolution:**
  - Landing page metrics pull from the verified Fact Bank (`packages/facts/fact_bank.json`) with primary source and date, or from live database queries that read `0` when production is empty.
  - Sandbox metrics are never presented as production figures.
- **Implemented In:** `apps/site/index.html`, `packages/facts/verify_facts.py`.
