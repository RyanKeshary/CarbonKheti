# Real-World Dependencies & Third-Party Approval Register

In strict accordance with **Rule 0** of CarbonKheti (*"If a real integration is not yet connected, the feature is disabled and labelled honestly, never simulated with fake success states"*), this document records the external regulatory, banking, and registry dependencies required for nationwide commercial launch, their current onboarding stage, and the architectural surface built to connect them.

---

## 1. Carbon Standards & Registry Issuance

| Dependency | Counterparty | Status | Platform Implementation |
|---|---|---|---|
| **Verra Project Registration (VM0051)** | Verra (Verified Carbon Standard) | **Awaiting Project Validation** | Platform implements full deterministic VM0051 v1.0 equations, IPCC 2019 scaling factors, uncertainty deduction, and 10% buffer contribution. Serial numbers are only displayed after real registry issuance; prior to issuance, credits are labelled strictly as *enrolled hectares, verified practice, estimated reduction with uncertainty, pre-issuance offtake agreement*. |
| **Bureau of Energy Efficiency (India CCTS)** | Ministry of Power / BEE | **Monitoring Phase 2 Offsets Protocol** | CCTS currently mandates 7 industrial compliance sectors. Agricultural offset integration rules are being drafted by BEE; platform tracks CCTS readiness. |
| **Validation and Verification Body (VVB)** | Accredited Auditor (e.g., Epic Sustainability, TÜV SÜD) | **Under Engagement** | Read-only auditor viewer with cryptographic SHA-256 hash chains and downloadable CSV/PDF audit packs is live. |

---

## 2. Banking & Payout Rails

| Dependency | Counterparty | Status | Platform Implementation |
|---|---|---|---|
| **Escrow Account & Payout API** | Razorpay X / Cashfree Payouts | **Merchant Kyc & Escrow Approval in Progress** | Payout service is configured for integer paise accounting and penny-drop bank verification. In sandbox/pre-approval mode, payouts are labelled honestly: *"Scheduled pending bank merchant verification"*. Zero simulated fake balances. |
| **Direct Beneficiary Penny-Drop** | NPCI / Partner Sponsor Bank | **Awaiting API Production Secret** | Penny-drop workflow transfers ₹1.00 (100 paise) to verify farmer account holder name before disbursing credit proceeds. |

---

## 3. Telecommunications & OTP Messaging

| Dependency | Counterparty | Status | Platform Implementation |
|---|---|---|---|
| **DLT SMS Template Registration** | Telecom Regulatory Authority of India (TRAI) / DLT Portal | **Template Content Approval in Progress** | Phone OTP authentication provides a transparent sandbox verification code (`8421`) for local testing while DLT headers (`CRBKHT`) undergo telecommunication compliance approval. |
| **WhatsApp Business API** | Meta Business Partner | **Awaiting Business Verification** | Webhook signature verification and notification queue architecture ready in `services/workers`. |

---

## 4. Legal & Regulatory Documents

| Dependency | Qualified Counsel | Status | Platform Implementation |
|---|---|---|---|
| **Farmer Project Participation Agreement** | Agricultural & Environmental Law Counsel | **Bilingual Drafts (English & Telugu)** | Agreement guarantees farmer retains 100% land ownership (Clause 5.1). Plain-language contract explainer with TTS is integrated. |
| **DPDP Act 2023 Compliance Review** | Data Protection Officer | **Audited for Purpose Limitation & Min. Data** | Granular opt-in consent for photos and stories; bank/Aadhaar data tokenized; grievance officer appointed (`grievance@carbonkheti.in`). |
