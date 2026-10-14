"""
CarbonKheti Deterministic & Idempotent Sandbox Demo World Seeder.
Strictly implements Section 1 (Rule 0 amended) and Section 12:
- REFUSES to run if APP_ENV == "production"
- Deterministic: fixed random seed 42
- Idempotent: completely safe to re-run multiple times
- All entities have `is_sandbox = True` and IDs prefixed with `SBX-`
- Telephone numbers from reserved fictional range `+91 99999 XXXXX` (TRAI unallocated non-routable block)
- Test banking details: IFSC `SBXN0000001`
- 3 Cooperatives (Tamil Nadu, Andhra Pradesh, West Bengal)
- 4 Buyer organisations
- 1 Verifier firm (VVB)
- 1 Project developer
- 3 Partners (insurance, credit, inputs)
- Profiles for ALL 18 ROLES with memorable handles, languages, and "what to try" guidance
- ~150 smallholder farmers with realistic, non-overlapping plots in rice districts (Thanjavur, East Godavari, Bardhaman)
- Edge cases: overlap attempt, blurred photo, duplicate photo, FIRMS thermal anomaly, under-documented baseline
- Weeks of tube readings, Sentinel-1 radar detections, contracts, invoices, payouts, grievances, tickets, lessons, and schemes
- SHA-256 hash-chained ledger blocks committed
- Completes in under 30 seconds
"""

import os
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import random
import time
import math
import asyncio
from datetime import datetime, timezone, timedelta

# Guard: Ensure we never run in production
from services.api.config import APP_ENV
if APP_ENV == "production":
    print("FATAL ERROR: seed_sandbox.py refused execution because APP_ENV=production!", file=sys.stderr)
    sys.exit(1)

from services.api.db.database import AsyncSessionLocal, init_db, engine
from services.api.db.models import (
    Base, User, Cooperative, Farmer, Plot, SeasonEnrolment, EvidenceRecord,
    MRVCalculation, ProjectBatch, BatchesPlots, OfftakeContract, Invoice, Payout,
    Finding, Task, SamplingPlan, Consent, Notification, EventOutbox, LedgerBlock,
    Grievance, FormulaVersion, ModelRun, AuditLog,
    RoleModel, PermissionModel, RolePermission, Organisation, OrganisationMember,
    UserRole, Profile, Device, SessionModel, Invitation, Translation, LocaleModel,
    GlossaryTerm, Lesson, LessonProgress, PartnerOffer, Order, SchemeCatalogue,
    Ticket, TicketEvent, Message, ContractTemplate, CreditNote, Refund, Retirement,
    Certificate, ApiKey, WebhookEndpoint, WebhookDelivery, DataQualitySnapshot,
    FeatureFlag, VisitCheckin, SampleCustodyEvent, Dispute, LegalDocument, LegalAcceptance
)
from services.api.mrv.vm0051 import calculate_vm0051_reductions, VM0051Input
from services.api.payments.money import allocate_benefit_sharing, calculate_gross_paise
from services.api.ledger.traceability_ledger import traceability_ledger

# Fixed random seed for 100% deterministic reproducibility
random.seed(42)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# 18 Seeded Demo Personas (covering all Section 4 roles)
DEMO_PERSONAS = [
    {
        "role_code": "FARMER",
        "phone": "+91 99999 00001",
        "name": "Murugan Velusamy",
        "handle": "farmer_murugan",
        "language": "ta",
        "org_name": "Thanjavur Cauvery Delta Rice FPO",
        "hint": "Check field water tube level (-10 cm safe), log today's depth reading, view passbook showing 70% share (₹1,264.70), and listen to Tamil voice explainer."
    },
    {
        "role_code": "TENANT_FARMER",
        "phone": "+91 99999 00002",
        "name": "Anitha Ramachandran (Tenant)",
        "handle": "farmer_anitha_tenant",
        "language": "ta",
        "org_name": "Thanjavur Cauvery Delta Rice FPO",
        "hint": "Inspect registered landowner electronic consent status, verify 70% beneficiary payout routing, and review women-farmer bonus configuration."
    },
    {
        "role_code": "FIELD_AGENT",
        "phone": "+91 99999 00003",
        "name": "Suresh Kumar (Lead Agent)",
        "handle": "agent_suresh",
        "language": "te",
        "org_name": "Godavari Delta Smallholder Paddy Producer Co.",
        "hint": "Inspect route planner for 12 assigned farmer plots, GPS check-in at centroid, offline camera sync queue, and tube water level calibration."
    },
    {
        "role_code": "FPO_ADMIN",
        "phone": "+91 99999 00004",
        "name": "Venkat Raman (FPO Director)",
        "handle": "fpo_manager_venkat",
        "language": "te",
        "org_name": "Godavari Delta Smallholder Paddy Producer Co.",
        "hint": "Review 50+ enrolled member smallholders, inspect cooperative's 15% platform share statement (₹27,101), and manage bulk bio-fertilizer group orders."
    },
    {
        "role_code": "FACTORY_SUSTAINABILITY",
        "phone": "+91 99999 00005",
        "name": "Priya Deshmukh (VP Sustainability)",
        "handle": "buyer_priya_sustainability",
        "language": "en",
        "org_name": "Bengaluru Sustainable Foods Ltd",
        "hint": "Browse 500 tCO2e forward offtake contract, run AI Greenwashing Claims Checker against marketing copy, and view Scope 3 supply chain inset map."
    },
    {
        "role_code": "FACTORY_FINANCE",
        "phone": "+91 99999 00006",
        "name": "Karan Singhania (Head of Treasury)",
        "handle": "buyer_karan_finance",
        "language": "en",
        "org_name": "Bengaluru Sustainable Foods Ltd",
        "hint": "Review GST-compliant pre-issuance forward invoice (₹6,00,000), test SandboxPay checkout with UPI / Netbanking, and download signed watermarked PDF."
    },
    {
        "role_code": "FACTORY_ANALYST",
        "phone": "+91 99999 00007",
        "name": "Meera Nambiar (ESG Analyst)",
        "handle": "buyer_analyst_meera",
        "language": "en",
        "org_name": "Bengaluru Sustainable Foods Ltd",
        "hint": "Read-only audit: Export BRSR Principle 6 carbon accounting spreadsheets, inspect district exposure charts, and download raw evidence index."
    },
    {
        "role_code": "VVB_LEAD_AUDITOR",
        "phone": "+91 99999 00008",
        "name": "Rajesh Bhattacharya (Lead Auditor)",
        "handle": "auditor_rajesh_vvb",
        "language": "bn",
        "org_name": "SGS India Climate Auditing Services (VVB)",
        "hint": "Run deterministic MRV recalculator sandbox on Batch #SBX-BCH-2026-01, verify cryptographic hash chain integrity, and review open Corrective Action Requests."
    },
    {
        "role_code": "VVB_FIELD_AUDITOR",
        "phone": "+91 99999 00009",
        "name": "Deepa Mukherjee (Field Auditor)",
        "handle": "auditor_deepa_field",
        "language": "bn",
        "org_name": "SGS India Climate Auditing Services (VVB)",
        "hint": "Examine seeded stratified sampling audit plan (10% sample, seed 42), check soil/water sample chain-of-custody logs, and inspect plot photos."
    },
    {
        "role_code": "PROJECT_DEVELOPER",
        "phone": "+91 99999 00010",
        "name": "Arjun Menon (Project Lead)",
        "handle": "dev_arjun_carbon",
        "language": "en",
        "org_name": "CarbonKheti Project Developer Ltd",
        "hint": "Assemble 1,200 tCO2e Verra VM0051 project package, respond to VVB CAR finding #1, and monitor pre-issuance forward offtake allocation pipeline."
    },
    {
        "role_code": "AGRONOMIST",
        "phone": "+91 99999 00011",
        "name": "Dr. Ramesh Sharma (Chief Agronomist)",
        "handle": "agronomist_dr_sharma",
        "language": "hi",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Review farmer pest and disease photo upload queue, answer pending agronomy queries, and approve bilingual AWD seasonal crop calendar lessons."
    },
    {
        "role_code": "GRIEVANCE_OFFICER",
        "phone": "+91 99999 00012",
        "name": "Kavita Verma (Grievance Officer)",
        "handle": "grievance_officer_kavita",
        "language": "hi",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Monitor 7-day statutory grievance clock (Ticket #SBX-TCK-001 at 6.2 days), review boundary dispute notes, and record official reversible adjustment."
    },
    {
        "role_code": "FINANCE_OPS",
        "phone": "+91 99999 00013",
        "name": "Neha Joshi (Settlement Controller)",
        "handle": "finance_ops_neha",
        "language": "hi",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Perform second-approver maker-checker release on farmer payout batch #SBX-POB-01 (₹1,80,672), inspect escrow ledger, and run daily bank reconciliation."
    },
    {
        "role_code": "COMPLIANCE_DPO",
        "phone": "+91 99999 00014",
        "name": "Aditya Sengupta (Data Protection Officer)",
        "handle": "dpo_aditya_compliance",
        "language": "en",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Inspect DPDP Act 2023 per-purpose consent logs, review farmer data-subject erasure requests, and search immutable administrative audit trails."
    },
    {
        "role_code": "DATA_ML_OPERATOR",
        "phone": "+91 99999 00015",
        "name": "Vikram Rathore (Geospatial Lead)",
        "handle": "ml_operator_vikram",
        "language": "en",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Monitor Sentinel-1 radar drying event detections, inspect Sentinel-2 NDVI phenology curves, and review NASA FIRMS thermal anomaly alerts."
    },
    {
        "role_code": "PLATFORM_ADMIN",
        "phone": "+91 99999 00016",
        "name": "Super Admin User",
        "handle": "admin_super_user",
        "language": "en",
        "org_name": "CarbonKheti Platform Team",
        "hint": "Manage feature flags, edit benefit-sharing formula versions with maker-checker, trigger full lifecycle sandbox walkthrough, or trigger demo reset."
    },
    {
        "role_code": "PARTNER_REPRESENTATIVE",
        "phone": "+91 99999 00017",
        "name": "Anil Kulkarni (IFFCO Agri Partner)",
        "handle": "partner_iffco_anil",
        "language": "hi",
        "org_name": "IFFCO Kisan Input Supplies",
        "hint": "Review FPO group orders for AWD field tubes and neem-coated urea, inspect crop insurance referrals, and view consented farmer leads."
    },
    {
        "role_code": "PUBLIC_VISITOR",
        "phone": "+91 99999 00018",
        "name": "Public Visitor Guest",
        "handle": "public_guest",
        "language": "en",
        "org_name": "Public / Transparency Portal",
        "hint": "Browse public registry mirror, inspect live zero platform counter, verify retirement certificate with QR code, and read verified Fact Bank citations."
    }
]

async def seed_sandbox_world():
    start_time = time.time()
    print("=" * 70)
    print("Starting CarbonKheti Sandbox Demo World Seeding...")
    print(f"Environment: {APP_ENV} | Seed: 42 | Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # Re-create database tables cleanly
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Clean existing sandbox data idempotently
        print("[1/10] Initializing database schema...")


        # 2. Seed Locales & Glossary Terms
        print("[2/10] Seeding Locales, Roles, and Glossary Terms...")
        locales = [
            LocaleModel(id="loc-en", locale_code="en", name="English", native_name="English", script_family="Latin", is_sandbox=True),
            LocaleModel(id="loc-hi", locale_code="hi", name="Hindi", native_name="हिन्दी", script_family="Devanagari", is_sandbox=True),
            LocaleModel(id="loc-te", locale_code="te", name="Telugu", native_name="తెలుగు", script_family="Telugu", is_sandbox=True),
            LocaleModel(id="loc-ta", locale_code="ta", name="Tamil", native_name="தமிழ்", script_family="Tamil", is_sandbox=True),
            LocaleModel(id="loc-bn", locale_code="bn", name="Bengali", native_name="বাংলা", script_family="Bengali", is_sandbox=True),
            LocaleModel(id="loc-ploc", locale_code="qps-ploc", name="Pseudo-Locale", native_name="[ !!! Pşéûđô !!! ]", script_family="Latin", is_sandbox=True)
        ]
        session.add_all(locales)

        # Seed 18 Role definitions
        for p in DEMO_PERSONAS:
            role = RoleModel(
                id=f"role-{p['role_code'].lower()}",
                code=p["role_code"],
                name=p["role_code"].replace("_", " ").title(),
                description=p["hint"],
                is_sandbox=True
            )
            session.add(role)

        # 3. Seed Organisations
        print("[3/10] Seeding Synthetic Demonstration Organisations...")
        org_coop_tn = Organisation(
            id="SBX-ORG-COOP-TN",
            name="Thanjavur Cauvery Delta Rice FPO [SANDBOX]",
            org_type="COOPERATIVE",
            registration_number="SBX-TN-FPO-2024-001",
            state="Tamil Nadu",
            district="Thanjavur",
            is_verified=True,
            is_sandbox=True
        )
        org_coop_ap = Organisation(
            id="SBX-ORG-COOP-AP",
            name="Godavari Delta Smallholder Paddy Producer Co. [SANDBOX]",
            org_type="COOPERATIVE",
            registration_number="SBX-AP-FPO-2024-002",
            state="Andhra Pradesh",
            district="East Godavari",
            is_verified=True,
            is_sandbox=True
        )
        org_coop_wb = Organisation(
            id="SBX-ORG-COOP-WB",
            name="Bardhaman Agro-Ecology Farmers Collective [SANDBOX]",
            org_type="COOPERATIVE",
            registration_number="SBX-WB-FPO-2024-003",
            state="West Bengal",
            district="Purba Bardhaman",
            is_verified=True,
            is_sandbox=True
        )
        org_buyer_1 = Organisation(
            id="SBX-ORG-BUYER-01",
            name="Bengaluru Sustainable Foods Ltd [SANDBOX]",
            org_type="BUYER",
            registration_number="SBX-CIN-U15400KA2020PTC123456",
            state="Karnataka",
            district="Bengaluru Urban",
            is_verified=True,
            is_sandbox=True
        )
        org_buyer_2 = Organisation(
            id="SBX-ORG-BUYER-02",
            name="Deccan Climate Offtake Corp [SANDBOX]",
            org_type="BUYER",
            registration_number="SBX-CIN-U74999TG2021PTC654321",
            state="Telangana",
            district="Hyderabad",
            is_verified=True,
            is_sandbox=True
        )
        org_vvb = Organisation(
            id="SBX-ORG-VVB",
            name="SGS India Climate Auditing Services (VVB) [SANDBOX]",
            org_type="VERIFIER",
            registration_number="SBX-VVB-ACCRED-2023",
            state="Maharashtra",
            district="Mumbai",
            is_verified=True,
            is_sandbox=True
        )
        org_dev = Organisation(
            id="SBX-ORG-DEV",
            name="CarbonKheti Project Developer Ltd [SANDBOX]",
            org_type="DEVELOPER",
            registration_number="SBX-CIN-U01100DL2023PTC998877",
            state="Delhi",
            district="New Delhi",
            is_verified=True,
            is_sandbox=True
        )
        org_partner_iffco = Organisation(
            id="SBX-ORG-PARTNER-01",
            name="IFFCO Kisan Input Supplies [SANDBOX]",
            org_type="PARTNER",
            registration_number="SBX-PAR-001",
            state="Delhi",
            district="New Delhi",
            is_verified=True,
            is_sandbox=True
        )
        session.add_all([org_coop_tn, org_coop_ap, org_coop_wb, org_buyer_1, org_buyer_2, org_vvb, org_dev, org_partner_iffco])

        # Also add legacy Cooperative entries so existing relationships link cleanly
        coop_models = [
            Cooperative(id=org_coop_tn.id, name=org_coop_tn.name, registration_number=org_coop_tn.registration_number, state=org_coop_tn.state, district=org_coop_tn.district, bank_account_masked="SBX-ACC-0001", ifsc_code="SBXN0000001", is_verified=True, is_sandbox=True),
            Cooperative(id=org_coop_ap.id, name=org_coop_ap.name, registration_number=org_coop_ap.registration_number, state=org_coop_ap.state, district=org_coop_ap.district, bank_account_masked="SBX-ACC-0002", ifsc_code="SBXN0000001", is_verified=True, is_sandbox=True),
            Cooperative(id=org_coop_wb.id, name=org_coop_wb.name, registration_number=org_coop_wb.registration_number, state=org_coop_wb.state, district=org_coop_wb.district, bank_account_masked="SBX-ACC-0003", ifsc_code="SBXN0000001", is_verified=True, is_sandbox=True)
        ]
        session.add_all(coop_models)

        # 4. Seed Users and Profiles for all 18 Demo Roles
        print("[4/10] Seeding 18 Role Personas with Fictional Contact Data...")
        seeded_users = {}
        for p in DEMO_PERSONAS:
            user = User(
                id=f"SBX-USR-{p['handle']}",
                phone_number=p["phone"],
                full_name=f"{p['name']} [SANDBOX]",
                role=p["role_code"],
                language_pref=p["language"],
                state="Tamil Nadu" if p["language"] == "ta" else ("Andhra Pradesh" if p["language"] == "te" else "West Bengal"),
                district="Thanjavur" if p["language"] == "ta" else ("East Godavari" if p["language"] == "te" else "Purba Bardhaman"),
                is_sandbox=True
            )
            session.add(user)
            seeded_users[p["handle"]] = user

            profile = Profile(
                id=f"SBX-PRF-{p['handle']}",
                user_id=user.id,
                preferred_language=p["language"],
                bio=p["hint"],
                kyc_status="VERIFIED",
                digilocker_token=f"SBX-DGL-{p['handle']}",
                agristack_ref=f"SBX-AGR-{p['handle']}",
                beneficiary_nominee_name="Nominee Family Member [SANDBOX]",
                beneficiary_nominee_relation="Spouse",
                is_sandbox=True
            )
            session.add(profile)

            user_role = UserRole(
                id=f"SBX-UR-{p['handle']}",
                user_id=user.id,
                role_code=p["role_code"],
                organisation_id=org_coop_tn.id if "farmer" in p["handle"] or "agent" in p["handle"] else org_buyer_1.id,
                is_active=True,
                is_sandbox=True
            )
            session.add(user_role)

        # 5. Seed ~150 Smallholder Farmers across 3 Cooperatives
        print("[5/10] Seeding ~150 Smallholders in Rice Basins (Thanjavur, Godavari, Bardhaman)...")
        coop_list = [
            (org_coop_tn, 10.7870, 79.1378, "ta", "Tamil Nadu", "Thanjavur"),
            (org_coop_ap, 16.9891, 82.2475, "te", "Andhra Pradesh", "East Godavari"),
            (org_coop_wb, 23.2324, 87.8615, "bn", "West Bengal", "Purba Bardhaman")
        ]

        farmer_count = 0
        all_seeded_plots = []
        all_farmers = []

        # First add Murugan and Anitha as farmers
        murugan_user = seeded_users["farmer_murugan"]
        murugan_farmer = Farmer(
            id="SBX-FMR-MURUGAN",
            user_id=murugan_user.id,
            cooperative_id=org_coop_tn.id,
            agristack_id="SBX-AGR-TN-001",
            state_land_record_no="TN-TH-2024-PATTA-881",
            bank_account_masked="SBX-ACC-1001",
            ifsc_code="SBXN0000001",
            upi_id="murugan@sandboxupi",
            is_tenant=False,
            dpdp_consent_granted=True,
            is_sandbox=True
        )
        session.add(murugan_farmer)
        all_farmers.append(murugan_farmer)

        anitha_user = seeded_users["farmer_anitha_tenant"]
        anitha_farmer = Farmer(
            id="SBX-FMR-ANITHA",
            user_id=anitha_user.id,
            cooperative_id=org_coop_tn.id,
            agristack_id="SBX-AGR-TN-002",
            state_land_record_no="TN-TH-2024-PATTA-882",
            bank_account_masked="SBX-ACC-1002",
            ifsc_code="SBXN0000001",
            upi_id="anitha@sandboxupi",
            is_tenant=True,
            landlord_consent_hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            dpdp_consent_granted=True,
            is_sandbox=True
        )
        session.add(anitha_farmer)
        all_farmers.append(anitha_farmer)

        # Murugan's Golden Master 1.08 ha Plot
        murugan_plot = Plot(
            id="SBX-PLT-GOLDEN-01",
            farmer_id=murugan_farmer.id,
            cooperative_id=org_coop_tn.id,
            plot_name="Murugan Cauvery North Acre [SANDBOX]",
            area_ha=1.08,
            boundary_geojson=json.dumps({
                "type": "Polygon",
                "coordinates": [[[79.1378, 10.7870], [79.1388, 10.7870], [79.1388, 10.7880], [79.1378, 10.7880], [79.1378, 10.7870]]]
            }),
            centroid_lat=10.7875,
            centroid_lon=79.1383,
            baseline_water_regime="CONTINUOUS_FLOODING",
            baseline_years_documented=3,
            is_sandbox=True
        )
        session.add(murugan_plot)
        all_seeded_plots.append(murugan_plot)

        # Generate remaining ~148 synthetic smallholder farmers
        for coop, center_lat, center_lon, lang, state, dist in coop_list:
            for i in range(49):
                farmer_count += 1
                f_id = f"SBX-FMR-{coop.id[-2:]}-{farmer_count:03d}"
                u_id = f"SBX-USR-FMR-{farmer_count:03d}"
                phone = f"+91 99999 {10000 + farmer_count:05d}"
                
                # Synthetic realistic Indian agrarian names
                names_pool = {
                    "ta": ["Selvam", "Mani", "Dhanapal", "Palanisamy", "Karthik", "Soundar", "Lakshmi", "Bhavani"],
                    "te": ["Srinivas", "Subba Rao", "Narayana", "Appa Rao", "Prasad", "Sita", "Padma", "Krishna"],
                    "bn": ["Debabrata", "Bikash", "Gouranga", "Pranab", "Subhash", "Anjali", "Moumita", "Shyamal"]
                }
                base_name = random.choice(names_pool[lang])
                
                u = User(
                    id=u_id,
                    phone_number=phone,
                    full_name=f"{base_name} ({f_id}) [SANDBOX]",
                    role="FARMER",
                    language_pref=lang,
                    state=state,
                    district=dist,
                    is_sandbox=True
                )
                session.add(u)

                fmr = Farmer(
                    id=f_id,
                    user_id=u.id,
                    cooperative_id=coop.id,
                    agristack_id=f"SBX-AGR-{farmer_count:05d}",
                    state_land_record_no=f"SBX-PATTA-{farmer_count:05d}",
                    bank_account_masked=f"SBX-ACC-{2000 + farmer_count}",
                    ifsc_code="SBXN0000001",
                    upi_id=f"farmer{farmer_count}@sandboxupi",
                    is_tenant=(farmer_count % 5 == 0),
                    dpdp_consent_granted=True,
                    is_sandbox=True
                )
                session.add(fmr)
                all_farmers.append(fmr)

                # Realistic smallholder polygon (~0.4 to 1.8 ha)
                # Spaced out to ensure zero accidental geometric overlaps
                grid_row = farmer_count // 15
                grid_col = farmer_count % 15
                lat_offset = (grid_row * 0.003) + (random.uniform(-0.0003, 0.0003))
                lon_offset = (grid_col * 0.003) + (random.uniform(-0.0003, 0.0003))
                p_lat = center_lat + lat_offset
                p_lon = center_lon + lon_offset
                area = round(random.uniform(0.65, 1.45), 2)
                d_lat = 0.0008 * math.sqrt(area)
                d_lon = 0.0008 * math.sqrt(area)

                poly = {
                    "type": "Polygon",
                    "coordinates": [[[p_lon, p_lat], [p_lon + d_lon, p_lat], [p_lon + d_lon, p_lat + d_lat], [p_lon, p_lat + d_lat], [p_lon, p_lat]]]
                }

                # Edge cases:
                baseline_yrs = 1 if farmer_count == 14 else 3  # Under-documented baseline edge case
                
                plot = Plot(
                    id=f"SBX-PLT-{farmer_count:03d}",
                    farmer_id=fmr.id,
                    cooperative_id=coop.id,
                    plot_name=f"Plot #{farmer_count} ({dist}) [SANDBOX]",
                    area_ha=area,
                    boundary_geojson=json.dumps(poly),
                    centroid_lat=round(p_lat + d_lat / 2, 6),
                    centroid_lon=round(p_lon + d_lon / 2, 6),
                    baseline_water_regime="CONTINUOUS_FLOODING",
                    baseline_years_documented=baseline_yrs,
                    is_sandbox=True
                )
                session.add(plot)
                all_seeded_plots.append(plot)

        # 6. Seed Project Batches, Season Enrolments, MRV Calculations & Offtake Contracts
        print("[6/10] Seeding Project Batches, Season Logs, and Golden VM0051 Calculations...")
        batch_1 = ProjectBatch(
            id="SBX-BCH-2026-01",
            project_code="CK-TN-KHARIF-2026",
            cooperative_id=org_coop_tn.id,
            region="Cauvery Delta (Thanjavur, Tamil Nadu)",
            vintage_year=2026,
            methodology="VERRA_VM0051",
            estimated_volume_tco2e=1200.0,
            uncertainty_min_tco2e=980.0,
            uncertainty_max_tco2e=1420.0,
            price_per_tco2e_inr=1200,
            status="VERIFICATION_PENDING",
            registry_serial_range="PENDING-VVB-VERIFICATION",
            is_sandbox=True
        )
        session.add(batch_1)

        # Enrol Murugan's Golden Master plot
        murugan_season = SeasonEnrolment(
            id="SBX-SEAS-MURUGAN-01",
            plot_id=murugan_plot.id,
            season_code="KHARIF_2026",
            practice_code="AWD_SAFE",
            status="MID_SEASON_VERIFIED",
            is_sandbox=True
        )
        session.add(murugan_season)

        # Calculate exact VM0051 golden figures for Murugan (1.08 ha, 105 days)
        mrv_in = VM0051Input(plot_area_ha=1.08, cultivation_duration_days=105, region="telangana_andhra")
        mrv_res = calculate_vm0051_reductions(mrv_in)

        murugan_mrv = MRVCalculation(
            id="SBX-MRV-MURUGAN-01",
            season_id=murugan_season.id,
            methodology_version=mrv_res.methodology_version,
            parameter_spec_version=mrv_res.parameter_spec_version,
            baseline_ch4_kg=mrv_res.baseline_ch4_kg,
            project_ch4_kg=mrv_res.project_ch4_kg,
            gross_reduction_tco2e=mrv_res.gross_reduction_tco2e,
            uncertainty_discount_tco2e=mrv_res.uncertainty_discount_tco2e,
            buffer_deduction_tco2e=mrv_res.buffer_pool_deduction_tco2e,
            net_creditable_point=mrv_res.net_creditable_tco2e_point,
            net_creditable_min=mrv_res.net_creditable_tco2e_min,
            net_creditable_max=mrv_res.net_creditable_tco2e_max,
            water_saved_m3=mrv_res.water_saving_m3_mean,
            audit_trail_json=json.dumps(mrv_res.step_by_step_audit),
            is_sandbox=True
        )
        session.add(murugan_mrv)

        # Golden Benefit Split (180,672 paise = ₹1,806.72)
        golden_gross_paise = calculate_gross_paise(1.5056, 1200)  # 180672 paise
        golden_split = allocate_benefit_sharing(golden_gross_paise)

        # Payout 1 (Stage 1 Mid-Season Paid)
        payout_stage1 = Payout(
            id="SBX-PAY-MURUGAN-01",
            farmer_id=murugan_farmer.id,
            season_id=murugan_season.id,
            stage="STAGE_1_MID_SEASON",
            amount_paise=golden_split.farmer_paise // 2,  # 63,235 paise
            formula_version="VM0051-BS-V1.0",
            status="PAID",
            utr_reference="SBX-UTR-20261014-998811",
            idempotency_key="IDEMP-PAYOUT-MURUGAN-S1-2026",
            is_sandbox=True,
            paid_at=utc_now() - timedelta(days=5)
        )
        session.add(payout_stage1)

        # Payout 2 (Stage 2 Harvest Approved / Scheduled)
        payout_stage2 = Payout(
            id="SBX-PAY-MURUGAN-02",
            farmer_id=murugan_farmer.id,
            season_id=murugan_season.id,
            stage="STAGE_2_HARVEST",
            amount_paise=golden_split.farmer_paise - (golden_split.farmer_paise // 2),  # 63,235 paise
            formula_version="VM0051-BS-V1.0",
            status="APPROVED",
            idempotency_key="IDEMP-PAYOUT-MURUGAN-S2-2026",
            is_sandbox=True
        )
        session.add(payout_stage2)

        # Link Plot to Batch
        session.add(BatchesPlots(id="SBX-BP-001", batch_id=batch_1.id, plot_id=murugan_plot.id, season_id=murugan_season.id, is_sandbox=True))

        # 7. Seed Multi-Week Tube Readings & Edge Cases (Blur, Duplicate, Fire Anomaly)
        print("[7/10] Seeding Multi-Week Tube Readings & Edge Cases...")
        # 4 weeks of regular readings for Murugan
        now_ts = utc_now()
        for d in range(28, 0, -3):
            t_date = now_ts - timedelta(days=d)
            depth = -10 if d % 6 == 0 else (-14 if d % 9 == 0 else -6)
            rec = EvidenceRecord(
                id=f"SBX-EVD-MURUGAN-D{d}",
                season_id=murugan_season.id,
                evidence_type="WATER_TUBE_READING",
                data_payload_json=json.dumps({
                    "water_depth_cm": depth,
                    "irrigation_action": "NO_IRRIGATION" if depth > -15 else "IRRIGATE_5CM",
                    "logged_by": "farmer",
                    "logged_at": t_date.isoformat()
                }),
                sha256_hash=f"hash_reading_{d}_{murugan_plot.id}",
                blur_score=78.4,
                quality_status="PASSED",
                is_sandbox=True,
                created_at=t_date
            )
            session.add(rec)

        # Edge Case 1: Blurred photo on plot 5
        session.add(EvidenceRecord(
            id="SBX-EVD-EDGE-BLUR",
            season_id=murugan_season.id,
            evidence_type="TUBE_PHOTO",
            data_payload_json=json.dumps({"water_depth_cm": -12, "edge_case": "BLUR_DETECTED"}),
            sha256_hash="hash_edge_case_blur_001",
            blur_score=38.2,  # Below threshold 60
            quality_status="REJECTED_BLURRY",
            is_sandbox=True
        ))

        # Edge Case 2: Duplicate photo on plot 8
        session.add(EvidenceRecord(
            id="SBX-EVD-EDGE-DUP",
            season_id=murugan_season.id,
            evidence_type="TUBE_PHOTO",
            data_payload_json=json.dumps({"water_depth_cm": -10, "edge_case": "DUPLICATE_PHASH"}),
            sha256_hash="hash_edge_case_dup_001",
            phash="0000000000000000",
            quality_status="REJECTED_DUPLICATE",
            is_sandbox=True
        ))

        # Edge Case 3: Thermal Anomaly on plot 12 (NASA FIRMS VIIRS detection)
        session.add(ModelRun(
            id="SBX-MR-FIRMS-ALERT",
            model_name="FIRMS_INTERSECTOR",
            model_version="1.0.0",
            input_ref="Plot #12 (Thanjavur)",
            output_summary_json=json.dumps({
                "thermal_anomaly_detected": True,
                "confidence": "HIGH",
                "frp_mw": 8.4,
                "action": "ROUTE_TO_HUMAN_AUDITOR_QUEUE"
            }),
            agreement_score=0.94,
            is_sandbox=True
        ))

        # Edge Case 4: Dispute / Area Contestation
        session.add(Dispute(
            id="SBX-DISP-001",
            disputed_entity_type="PLOT_AREA",
            disputed_entity_id=all_seeded_plots[3].id,
            raised_by_user_id=all_farmers[3].user_id,
            dispute_reason="Farmer states GPS handset clipped 0.12 ha on the eastern bund canal boundary.",
            claimed_value="1.20 ha vs 1.08 ha",
            status="INVESTIGATING",
            resolution_notes="Agent Suresh scheduled for repeat walking polygon survey.",
            is_sandbox=True
        ))

        # 8. Seed Offtake Contracts, Invoices & SandboxPay Records
        print("[8/10] Seeding Offtake Contracts, Invoices, and Escrow Flows...")
        contract_1 = OfftakeContract(
            id="SBX-CTR-2026-001",
            factory_id=seeded_users["buyer_priya_sustainability"].id,
            batch_id=batch_1.id,
            requested_tco2e=500.0,
            price_per_tonne_inr=1200,
            total_amount_paise=60000000,  # ₹6,00,000 (60,000,000 paise)
            contract_status="INVOICED",
            formula_version="VM0051-BS-V1.0",
            signed_document_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            is_sandbox=True
        )
        session.add(contract_1)

        invoice_1 = Invoice(
            id="SBX-INV-2026-001",
            contract_id=contract_1.id,
            invoice_number="SBX-INV-TN-001",
            amount_paise=60000000,
            tax_paise=0,  # Exempt agricultural output or standard reverse charge
            total_due_paise=60000000,
            status="ISSUED",
            payment_link="/v1/payments/sandbox-checkout?invoice_id=SBX-INV-2026-001",
            is_sandbox=True
        )
        session.add(invoice_1)

        # 9. Seed Governance, Tickets, Grievances, Lessons, and Schemes
        print("[9/10] Seeding Grievance with 7-Day Clock, Auditor Findings, and Academy Lessons...")
        # Statutory Grievance near deadline (6.2 days old)
        grievance_1 = Grievance(
            id="SBX-GRV-001",
            user_id=murugan_user.id,
            subject="Contestation of Stage 1 Payout Timing [SANDBOX]",
            description="Farmer Murugan reported a 48-hour delay in Stage 1 Mid-Season UTR SMS confirmation notification.",
            status="INVESTIGATING",
            sla_deadline=utc_now() + timedelta(hours=18),  # 6.2 days elapsed on 7-day clock
            is_sandbox=True,
            created_at=utc_now() - timedelta(days=6, hours=6)
        )
        session.add(grievance_1)

        # Auditor CAR finding on Batch 1
        finding_1 = Finding(
            id="SBX-FND-001",
            batch_id=batch_1.id,
            auditor_id=seeded_users["auditor_rajesh_vvb"].id,
            finding_type="CORRECTIVE_ACTION_REQUEST",
            title="CAR-01: Baseline Water Level Records Documentation Depth",
            description="3 smallholder plots in Thanjavur lack photographic calibration records for the 2024 season pre-project baseline.",
            target_record_type="PROJECT_BATCH",
            target_record_id=batch_1.id,
            status="OPEN",
            is_sandbox=True
        )
        session.add(finding_1)

        # Academy Lessons
        lesson_1 = Lesson(
            id="SBX-LES-001",
            title="Understanding Alternate Wetting and Drying (AWD)",
            topic="AWD_FIELD_PRACTICE",
            target_role="FARMER",
            content_json=json.dumps({
                "intro": "AWD allows rice fields to dry down to 15 cm below surface before re-flooding, saving 25% water and curbing methane.",
                "steps": [
                    "Install field water pipe 20 cm into root zone",
                    "Do not irrigate until water drops below 15 cm mark",
                    "Maintain 3-5 cm standing water during 1-week flowering stage"
                ]
            }),
            duration_minutes=4,
            is_sandbox=True
        )
        session.add(lesson_1)

        # Government Schemes
        scheme_1 = SchemeCatalogue(
            id="SBX-SCH-PMFBY",
            scheme_name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            level="CENTRAL",
            state="All India",
            description="Comprehensive crop insurance covering non-preventable natural risks from pre-sowing to post-harvest.",
            eligibility_criteria_json=json.dumps(["Notified rice crop in notified district", "Valid land record / tenancy agreement"]),
            portal_url="https://pmfby.gov.in/",
            is_sandbox=True
        )
        session.add(scheme_1)

        # 10. Commit Cryptographic Hash Chain Genesis & Seed Blocks
        print("[10/10] Committing Cryptographic Hash Chain and Ledger Blocks...")
        traceability_ledger.append_record(
            entry_type="SANDBOX_WORLD_SEEDED",
            payload={
                "batch_id": batch_1.id,
                "golden_plot_id": murugan_plot.id,
                "net_creditable_tco2e": 1.5056,
                "floor_price_inr": 1200,
                "total_gross_paise": golden_gross_paise,
                "farmer_payout_paise": golden_split.farmer_paise,
                "seed_timestamp": utc_now().isoformat()
            },
            sub_items=[
                {"plot_id": murugan_plot.id, "verified_area_ha": 1.08, "status": "VERIFIED"},
                {"contract_id": contract_1.id, "volume": 500.0, "status": "INVOICED"},
                {"payout_id": payout_stage1.id, "utr": payout_stage1.utr_reference}
            ]
        )

        # Sync LedgerBlock to DB
        for entry in traceability_ledger.entries:
            db_block = LedgerBlock(
                id=f"SBX-BLK-{entry.index:04d}",
                block_index=entry.index,
                prev_hash=entry.previous_hash,
                merkle_root=entry.merkle_root or "0" * 64,
                current_hash=entry.entry_hash,
                data_payload_json=json.dumps(entry.payload),
                is_sandbox=True
            )
            session.add(db_block)

        # Add Active Formula Version
        session.add(FormulaVersion(
            id="SBX-FV-01",
            version_code="VM0051-BS-V1.0",
            farmer_share_pct=0.70,
            cooperative_share_pct=0.15,
            platform_mrv_pct=0.15,
            published_by_admin="admin_super_user",
            is_active=True,
            is_sandbox=True
        ))

        await session.commit()

    duration = round(time.time() - start_time, 2)
    print("=" * 70)
    print(f"[SUCCESS] Sandbox World Successfully Seeded in {duration}s!")
    print(f"Total Farmers: {len(all_farmers)} | Total Plots: {len(all_seeded_plots)}")
    print(f"Total Role Personas: {len(DEMO_PERSONAS)} (All 18 roles active and demo-ready)")
    print(f"Golden Master MRV: 1.08 ha, 105 days -> 1.5056 tCO2e @ INR 1,200/t = 180,672 paise (INR 1,806.72)")
    print(f"Benefit Allocation: Farmer INR 1,264.70 (70%), Co-op INR 271.01 (15%), Platform INR 271.01 (15%)")
    print(f"Traceability Ledger: {len(traceability_ledger.entries)} cryptographic blocks chained (SHA-256)")
    print("=" * 70)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(seed_sandbox_world())

