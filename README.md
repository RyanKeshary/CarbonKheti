# CarbonKheti &bull; Every Ton Has a Face

> **Tagline:** *Factories pay to cut carbon. Farmers get paid to grow it back.*  
> **Standard:** Verra VM0051 (Improved Management in Rice Production Systems v1.0) &bull; CORSIA Eligible

---

## 0. The One Rule That Overrides Everything

**Nothing in this product may be fake.**

- **Zero Fake Seed Rows:** The database ships with zero sample farmers, zero fake payouts, zero invented credits, and zero fictitious testimonials. The only seed data is real, primary-sourced reference tables (Indian states, pilot districts, crop calendars, practice catalogues, standard methodologies).
- **Honest Empty States:** Empty states are real ("*No plots enrolled yet. Add your first plot.*") with a clear next action.
- **Fact Bank Verification:** Every number shown to a user is either computed from active database records or cited from the 16 primary sources in `packages/facts/facts.json`, complete with source URLs and "as of" dates.
- **Honest Disabled States:** When external approvals (such as bank escrow merchant approval or Verra registry issuance) are pending, features are labeled honestly ("*Payouts open once your cooperative is verified*"). We never simulate fake success states.
- **Uncertainty Transparency:** The system reports 95% confidence intervals and VM0051 uncertainty discounts, never an unsupported point estimate.
- **Real Traceability:** Credits are never labelled as "issued" or "sold" until backed by an official registry serial number. Prior to issuance, the product speaks in honest terms: *enrolled hectares, verified practice, estimated reduction with uncertainty range, pre-issuance offtake agreement*.

---

## 1. System Architecture

CarbonKheti is organized as an auditable, high-performance monorepo:

```
├── apps/
│   ├── site/                   # Public landing page (14 complete sections, calm paper aesthetic, live VM0051 calculator)
│   └── web/                    # Authenticated PWA (Farmer Passbook, AWD tube logger, photo QA, Cooperative & Factory portals)
├── services/
│   ├── api/                    # FastAPI (Python 3.12), async, Pydantic v2, OpenAPI at /v1
│   │   ├── mrv/                # Deterministic Verra VM0051 v1.0 engine & IPCC 2019 Refinement tables
│   │   ├── ml/                 # Sentinel-1 radar detector, FIRMS fire intersector, pHash/blur QA, geometry overlap
│   │   ├── ai/                 # Groq LLM proxy with circuit breaker, grounded RAG agronomy advisor, contract explainer
│   │   ├── ledger/             # Append-only SHA-256 cryptographic hash-chained traceability ledger
│   │   ├── payments/           # Integer-paise payout service (Razorpay X / Cashfree interface with penny-drop)
│   │   ├── audit/              # Downloadable CSV & PDF audit pack generator
│   │   └── db/                 # PostgreSQL 16 + PostGIS models (with async SQLite fallback)
│   └── workers/                # Satellite ingestion and reconciliation background workers
├── packages/
│   ├── facts/                  # Fact Bank (facts.json) & CI validation script (verify_facts.py)
│   └── ui/                     # Calm paper-like aesthetic design tokens (tokens.css) meeting WCAG AA
├── docs/
│   ├── real-world-dependencies.md # Detailed registry, bank, and regulatory approval tracking
│   ├── data-dictionary.md      # Complete database schema reference
│   └── model_cards/            # Model cards for Sentinel-1, anomaly scoring, and FIRMS intersector
├── infra/                      # Docker Compose, PostGIS 16, Redis 7, Caddy / Nginx, .env.example
└── tests/                      # Automated pytest suite (MRV math, overlap checks, ledger tampering, RAG citations)
```

---

## 2. Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- Node.js 20+ and npm

### 1. Run Verification & Tests
```bash
# Validate the Fact Bank URLs and schema
npm run verify:facts

# Run automated tests covering VM0051 math, ledger tamper-proofing, and geometry overlap
npm run test:api
```

### 2. Start Services Locally
```bash
# Terminal 1: Start FastAPI backend (runs on http://localhost:8000)
npm run dev:api

# Terminal 2: Start public landing page (runs on http://localhost:3000)
npm run dev:site

# Terminal 3: Start authenticated PWA app (runs on http://localhost:3001)
npm run dev:web
```

Or run everything simultaneously with a single command:
```bash
npm run dev
```

---

## 3. Core Features by Role

### Farmer App (PWA &bull; Voice-Guided &bull; Offline-Capable)
- **Phone OTP Authentication:** Verified against registered phone numbers.
- **Real Carbon Passbook:** Shows enrolled hectares, AWD practice milestones, verified status, and contractual payout schedule. Zero fake balances.
- **AWD Water Tube Logger:** Records perforated field tube depth with safe AWD zone indicator ($-15\text{ cm}$ threshold).
- **Geo-Tagged Photo Capture:** On-device Laplacian variance checks for blurry images; validates photo GPS is within $300\text{ m}$ of plot centroid; perceptual hash (dHash) prevents duplicate photo reuse.
- **Grounded Agronomy Assistant:** Voice and text assistant powered by Groq LLM with strict RAG over IRRI Rice Knowledge Bank, ICAR bulletins, and VM0051 methodology. Strictly refuses unauthorized pesticide prescribing.
- **Plain-Language Contract Explainer:** Explains Clause 4.2 (70% revenue share) and Clause 5.1 (farmer retains 100% land ownership) with voice read-aloud (TTS).

### Cooperative / Field Agent Dashboard
- **Bulk Enrolment & Baseline Surveys:** Captures 3 prior seasons of continuous flooding to prove additionality.
- **Conflict Safeguard:** Automated PostGIS/Shapely polygon overlap detector blocks double counting.
- **Offline Sync Queue:** Local IndexedDB caching for remote rural field visits with background sync.

### Factory Buyer Portal
- **Project Marketplace:** Live batches listed with 95% confidence uncertainty ranges and honest pre-issuance offtake status.
- **Scope 3 Traceability:** Maps carbon credits directly to verified smallholder farmers in sourcing regions.
- **Audit Pack Exporter:** Downloads signed PDF verification certificates and plot-level CSV audit logs.

### Auditor View & Traceability Ledger
- **Cryptographic Hash Chain:** Every plot enrolment, MRV calculation, and payout tranche is sealed into an append-only SHA-256 hash chain with instant tamper-detection verification.

---

## 4. Scientific MRV: Verra VM0051 v1.0

The calculation engine in `services/api/mrv/vm0051.py` implements the exact equations:
1. **Baseline Daily Emission:**  
   $$EF_{\text{base}} = EF_c \times SF_w \times SF_p \times SF_o$$  
   Using IPCC 2019 Refinement (Vol. 4, Ch. 5, Table 5.11: $EF_c = 1.30\text{ kg CH}_4/\text{ha/day}$, Table 5.12: $SF_w = 1.00$).
2. **Project Daily Emission (Safe AWD):**  
   $$EF_{\text{proj}} = EF_c \times 0.52 \times 1.00 \times 1.00$$  
   Using Table 5.12 scaling factor $SF_w = 0.52$ for multiple aeration.
3. **Seasonal Methane Reduction & GWP Conversion:**  
   $$\Delta \text{CH}_4 = (EF_{\text{base}} - EF_{\text{proj}}) \times \text{days} \times \text{area}$$  
   $$\text{Gross } t\text{CO}_2e = (\Delta \text{CH}_4 / 1000) \times 28.0 \quad (\text{IPCC AR5 } GWP_{\text{CH}_4})$$
4. **Uncertainty Propagation & Discounts:**  
   Quadrature error propagation ($35\%$ baseline uncertainty $\oplus$ $25\%$ practice uncertainty). Discounts deducted per VM0051 Section 8.4.
5. **Pooled Buffer Contribution:**  
   $10\%$ dedicated to the Verra non-permanence pooled risk buffer account.
6. **Benefit Sharing Formula:**  
   $70\%$ directly to the smallholder farmer, $15\%$ to the local cooperative, $15\%$ for MRV, satellite tasking, and independent audit fees.

---

## 5. Security & Privacy (DPDP Act 2023)

- **Granular Consent:** Explicit opt-in consent recorded with cryptographic timestamps before any field photo or narrative is published.
- **Data Minimization:** Aadhaar numbers are never stored in plain text; phone numbers and bank account numbers are tokenized.
- **Data Residency:** All data stored and processed within Indian territory.
- **Grievance Redressal:** Designated Grievance Officer accessible via `grievance@carbonkheti.in` with a statutory 7-day response timeline.

---

## 6. Real-World Dependencies

Where real-world integrations await regulatory, registry, or banking clearance, they are documented thoroughly in [`docs/real-world-dependencies.md`](./docs/real-world-dependencies.md).
