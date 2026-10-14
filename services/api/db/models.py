"""
SQLAlchemy ORM Data Models for CarbonKheti.
Section 1 & Section 6 Mandate:
- Real production vs hard-separated sandbox (is_sandbox = True on all demonstration entities)
- All financial balances stored in integer paise (BigInteger)
- Timestamps stored as timezone-aware datetimes
- Complete event outbox, ledger blocks, consents, tasks, sampling plans, findings, and invoices
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey, BigInteger, DateTime, Index
)
from sqlalchemy.orm import relationship
from .database import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

ALL_ROLES = [
    "FARMER",
    "TENANT_FARMER",
    "FIELD_AGENT",
    "FPO_ADMIN",
    "FACTORY_SUSTAINABILITY",
    "FACTORY_FINANCE",
    "FACTORY_ANALYST",
    "VVB_LEAD_AUDITOR",
    "VVB_FIELD_AUDITOR",
    "PROJECT_DEVELOPER",
    "AGRONOMIST",
    "GRIEVANCE_OFFICER",
    "FINANCE_OPS",
    "COMPLIANCE_DPO",
    "DATA_ML_OPERATOR",
    "PLATFORM_ADMIN",
    "PARTNER_REPRESENTATIVE",
    "PUBLIC_VISITOR"
]

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False)  # "FARMER", "COOPERATIVE_AGENT", "FACTORY_BUYER", "AUDITOR", "ADMIN"
    language_pref = Column(String(10), default="en")
    state = Column(String(60), nullable=True)
    district = Column(String(60), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    farmer_profile = relationship("Farmer", back_populates="user", uselist=False)
    consents = relationship("Consent", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    grievances = relationship("Grievance", back_populates="user")

class Cooperative(Base):
    __tablename__ = "cooperatives"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(160), nullable=False)
    registration_number = Column(String(80), unique=True, nullable=False)
    state = Column(String(60), nullable=False)
    district = Column(String(60), nullable=False)
    bank_account_masked = Column(String(40), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    farmers = relationship("Farmer", back_populates="cooperative")
    plots = relationship("Plot", back_populates="cooperative")
    batches = relationship("ProjectBatch", back_populates="cooperative")

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    cooperative_id = Column(String(36), ForeignKey("cooperatives.id"), nullable=True)
    agristack_id = Column(String(60), nullable=True)
    state_land_record_no = Column(String(80), nullable=True)
    bank_account_masked = Column(String(40), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    upi_id = Column(String(80), nullable=True)
    is_tenant = Column(Boolean, default=False)
    landlord_consent_hash = Column(String(64), nullable=True)
    dpdp_consent_granted = Column(Boolean, default=False)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="farmer_profile")
    cooperative = relationship("Cooperative", back_populates="farmers")
    plots = relationship("Plot", back_populates="farmer")
    payouts = relationship("Payout", back_populates="farmer")

class Plot(Base):
    __tablename__ = "plots"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    farmer_id = Column(String(36), ForeignKey("farmers.id"), nullable=False)
    cooperative_id = Column(String(36), ForeignKey("cooperatives.id"), nullable=True)
    plot_name = Column(String(100), nullable=False)
    area_ha = Column(Float, nullable=False)
    boundary_geojson = Column(Text, nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    baseline_water_regime = Column(String(40), default="CONTINUOUS_FLOODING")
    baseline_years_documented = Column(Integer, default=3)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    farmer = relationship("Farmer", back_populates="plots")
    cooperative = relationship("Cooperative", back_populates="plots")
    seasons = relationship("SeasonEnrolment", back_populates="plot")

class SeasonEnrolment(Base):
    __tablename__ = "season_enrolments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    plot_id = Column(String(36), ForeignKey("plots.id"), nullable=False)
    season_code = Column(String(30), nullable=False)
    practice_code = Column(String(30), default="AWD_SAFE")
    status = Column(String(40), default="ENROLLED")
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    plot = relationship("Plot", back_populates="seasons")
    evidence_records = relationship("EvidenceRecord", back_populates="season")
    mrv_calculation = relationship("MRVCalculation", back_populates="season", uselist=False)
    payouts = relationship("Payout", back_populates="season")

class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    season_id = Column(String(36), ForeignKey("season_enrolments.id"), nullable=False)
    evidence_type = Column(String(30), nullable=False)
    data_payload_json = Column(Text, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    phash = Column(String(32), nullable=True)
    blur_score = Column(Float, nullable=True)
    quality_status = Column(String(30), default="PASSED")
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    season = relationship("SeasonEnrolment", back_populates="evidence_records")

class MRVCalculation(Base):
    __tablename__ = "mrv_calculations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    season_id = Column(String(36), ForeignKey("season_enrolments.id"), unique=True, nullable=False)
    methodology_version = Column(String(30), default="VM0051 v1.0")
    parameter_spec_version = Column(String(30), default="VM0051-PAR-2026-V1")
    baseline_ch4_kg = Column(Float, nullable=False)
    project_ch4_kg = Column(Float, nullable=False)
    gross_reduction_tco2e = Column(Float, nullable=False)
    uncertainty_discount_tco2e = Column(Float, default=0.0)
    buffer_deduction_tco2e = Column(Float, default=0.0)
    net_creditable_point = Column(Float, nullable=False)
    net_creditable_min = Column(Float, nullable=False)
    net_creditable_max = Column(Float, nullable=False)
    water_saved_m3 = Column(Float, default=0.0)
    audit_trail_json = Column(Text, nullable=False)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    season = relationship("SeasonEnrolment", back_populates="mrv_calculation")

class ProjectBatch(Base):
    __tablename__ = "project_batches"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_code = Column(String(40), nullable=False)
    cooperative_id = Column(String(36), ForeignKey("cooperatives.id"), nullable=False)
    region = Column(String(100), nullable=False)
    vintage_year = Column(Integer, nullable=False)
    methodology = Column(String(40), default="VERRA_VM0051")
    estimated_volume_tco2e = Column(Float, nullable=False)
    uncertainty_min_tco2e = Column(Float, nullable=False)
    uncertainty_max_tco2e = Column(Float, nullable=False)
    price_per_tco2e_inr = Column(Integer, nullable=False)
    status = Column(String(40), default="ENROLLING")
    registry_serial_range = Column(String(120), nullable=True)
    registry_url = Column(String(255), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    cooperative = relationship("Cooperative", back_populates="batches")
    offtake_contracts = relationship("OfftakeContract", back_populates="batch")
    findings = relationship("Finding", back_populates="batch")

class BatchesPlots(Base):
    __tablename__ = "batches_plots"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    batch_id = Column(String(36), ForeignKey("project_batches.id"), nullable=False)
    plot_id = Column(String(36), ForeignKey("plots.id"), nullable=False)
    season_id = Column(String(36), ForeignKey("season_enrolments.id"), nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class OfftakeContract(Base):
    __tablename__ = "offtake_contracts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    factory_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    batch_id = Column(String(36), ForeignKey("project_batches.id"), nullable=False)
    requested_tco2e = Column(Float, nullable=False)
    price_per_tonne_inr = Column(Integer, nullable=False)
    total_amount_paise = Column(BigInteger, nullable=False)
    contract_status = Column(String(40), default="DRAFT")  # DRAFT, SENT, SIGNED, INVOICED, FUNDED, FULFILLING, DELIVERED, CLOSED
    formula_version = Column(String(30), default="VM0051-BS-V1.0")
    signed_document_hash = Column(String(64), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    batch = relationship("ProjectBatch", back_populates="offtake_contracts")
    invoices = relationship("Invoice", back_populates="contract")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    contract_id = Column(String(36), ForeignKey("offtake_contracts.id"), nullable=False)
    invoice_number = Column(String(40), unique=True, nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    tax_paise = Column(BigInteger, default=0)
    total_due_paise = Column(BigInteger, nullable=False)
    status = Column(String(30), default="ISSUED")  # DRAFT, ISSUED, PAYMENT_PENDING, PAID, FAILED, REFUNDED, CANCELLED
    payment_link = Column(String(255), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    contract = relationship("OfftakeContract", back_populates="invoices")

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    farmer_id = Column(String(36), ForeignKey("farmers.id"), nullable=False)
    season_id = Column(String(36), ForeignKey("season_enrolments.id"), nullable=False)
    stage = Column(String(30), nullable=False)  # "STAGE_1_MID_SEASON", "STAGE_2_HARVEST"
    amount_paise = Column(BigInteger, nullable=False)
    formula_version = Column(String(30), default="VM0051-BS-V1.0", nullable=False)
    status = Column(String(40), default="SCHEDULED")  # SCHEDULED, AWAITING_APPROVAL, APPROVED, PROCESSING, PAID, FAILED
    utr_reference = Column(String(60), nullable=True)
    idempotency_key = Column(String(80), unique=True, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    farmer = relationship("Farmer", back_populates="payouts")
    season = relationship("SeasonEnrolment", back_populates="payouts")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    batch_id = Column(String(36), ForeignKey("project_batches.id"), nullable=False)
    auditor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    finding_type = Column(String(40), nullable=False)  # "CLARIFICATION_REQUEST", "CORRECTIVE_ACTION_REQUEST", "FORWARD_ACTION"
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    target_record_type = Column(String(40), nullable=True)
    target_record_id = Column(String(36), nullable=True)
    status = Column(String(30), default="OPEN")  # "OPEN", "RESPONDED", "CLOSED"
    response_text = Column(Text, nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    batch = relationship("ProjectBatch", back_populates="findings")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    assigned_to_role = Column(String(30), nullable=False)  # "COOPERATIVE_AGENT", "AUDITOR", "ADMIN"
    assigned_to_user_id = Column(String(36), nullable=True)
    task_type = Column(String(40), nullable=False)  # "FIELD_VISIT", "OVERLAP_REVIEW", "PAYOUT_APPROVAL", "ANOMALY_CHECK"
    priority = Column(String(20), default="MEDIUM")
    title = Column(String(160), nullable=False)
    details_json = Column(Text, nullable=True)
    status = Column(String(30), default="PENDING")  # "PENDING", "IN_PROGRESS", "COMPLETED", "DISMISSED"
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class SamplingPlan(Base):
    __tablename__ = "sampling_plans"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    batch_id = Column(String(36), ForeignKey("project_batches.id"), nullable=False)
    seed = Column(Integer, nullable=False)
    sampling_rate_pct = Column(Float, default=10.0)
    selected_plot_ids_json = Column(Text, nullable=False)
    stratification_criteria = Column(String(100), default="VILLAGE_STRATIFIED")
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    purpose = Column(String(60), nullable=False)  # "MRV_FIELD_MONITORING", "SATELLITE_VERIFICATION", "BENEFIT_PAYOUT", "PUBLIC_IMPACT_STORY"
    notice_version = Column(String(30), default="DPDP-2023-V1.0")
    granted = Column(Boolean, default=True)
    granted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="consents")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    channel = Column(String(20), default="IN_APP")  # "IN_APP", "SMS", "WHATSAPP", "EMAIL"
    title = Column(String(160), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    delivery_status = Column(String(20), default="DELIVERED")
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="notifications")

class EventOutbox(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_type = Column(String(60), nullable=False)  # "PLOT_REGISTERED", "READING_LOGGED", "OFFTAKE_SIGNED", "PAYOUT_PAID", etc.
    aggregate_type = Column(String(40), nullable=False)
    aggregate_id = Column(String(36), nullable=False)
    payload_json = Column(Text, nullable=False)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class LedgerBlock(Base):
    __tablename__ = "ledger_blocks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    block_index = Column(Integer, nullable=False, unique=True)
    prev_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    data_payload_json = Column(Text, nullable=False)
    opentimestamps_proof = Column(Text, nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN")  # OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, CLOSED
    sla_deadline = Column(DateTime(timezone=True), nullable=False)  # 7-day clock
    resolution_notes = Column(Text, nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="grievances")

class FormulaVersion(Base):
    __tablename__ = "formula_versions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    version_code = Column(String(40), unique=True, nullable=False)  # "VM0051-BS-V1.0"
    farmer_share_pct = Column(Float, nullable=False)
    cooperative_share_pct = Column(Float, nullable=False)
    platform_mrv_pct = Column(Float, nullable=False)
    published_by_admin = Column(String(36), nullable=False)
    published_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    model_name = Column(String(60), nullable=False)  # "SENTINEL1_WATER_DETECTOR", "FIRMS_INTERSECTOR", "PHOTO_GATE", "ANOMALY_SCORER"
    model_version = Column(String(20), nullable=False)
    input_ref = Column(String(100), nullable=False)
    output_summary_json = Column(Text, nullable=False)
    agreement_score = Column(Float, nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), nullable=True)
    action = Column(String(60), nullable=False)
    resource_type = Column(String(60), nullable=False)
    resource_id = Column(String(60), nullable=False)
    details_json = Column(Text, nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

# ==============================================================================
# SECTION 10 & SECTION 4 EXTENSIONS: ROLES, GOVERNANCE, I18N, COMMERCE, COMPLIANCE
# ==============================================================================

class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(40), unique=True, nullable=False)  # e.g. "FARMER", "TENANT_FARMER", "FIELD_AGENT", "FPO_ADMIN", ...
    name = Column(String(80), nullable=False)
    description = Column(String(255), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class PermissionModel(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(60), unique=True, nullable=False)  # "plot:read", "payout:approve", etc.
    name = Column(String(100), nullable=False)
    category = Column(String(40), nullable=False)

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id"), nullable=False)

class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(160), nullable=False)
    org_type = Column(String(40), nullable=False)  # "COOPERATIVE", "BUYER", "VERIFIER", "DEVELOPER", "PARTNER", "PLATFORM"
    registration_number = Column(String(80), nullable=False)
    state = Column(String(60), nullable=True)
    district = Column(String(60), nullable=True)
    is_verified = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class OrganisationMember(Base):
    __tablename__ = "organisation_members"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_in_org = Column(String(40), default="MEMBER")
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_code = Column(String(40), nullable=False)
    organisation_id = Column(String(36), ForeignKey("organisations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    preferred_language = Column(String(10), default="en")
    avatar_url = Column(String(255), nullable=True)
    bio = Column(String(255), nullable=True)
    kyc_status = Column(String(30), default="PENDING")
    digilocker_token = Column(String(100), nullable=True)
    agristack_ref = Column(String(80), nullable=True)
    beneficiary_nominee_name = Column(String(120), nullable=True)
    beneficiary_nominee_relation = Column(String(60), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    device_fingerprint = Column(String(100), nullable=False)
    device_model = Column(String(100), nullable=True)
    app_version = Column(String(20), default="3.0.0")
    last_sync_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    pending_sync_count = Column(Integer, default=0)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), nullable=False)
    device_id = Column(String(36), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id"), nullable=False)
    email_or_phone = Column(String(80), nullable=False)
    role_code = Column(String(40), nullable=False)
    invited_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    status = Column(String(30), default="PENDING")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Translation(Base):
    __tablename__ = "translations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(36), nullable=False)
    field_name = Column(String(40), nullable=False)
    locale = Column(String(10), nullable=False)
    translated_value = Column(Text, nullable=False)
    status = Column(String(30), default="REVIEWED")  # "MACHINE", "REVIEWED", "APPROVED"
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class LocaleModel(Base):
    __tablename__ = "locales"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    locale_code = Column(String(10), unique=True, nullable=False)  # "en", "hi", "te", "ta", "bn", "qps-ploc"
    name = Column(String(60), nullable=False)
    native_name = Column(String(60), nullable=False)
    script_family = Column(String(40), nullable=False)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    term_key = Column(String(60), nullable=False)
    locale = Column(String(10), nullable=False)
    definition = Column(Text, nullable=False)
    context = Column(String(100), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(160), nullable=False)
    topic = Column(String(60), nullable=False)  # "AWD_FIELD_PRACTICE", "TUBE_READING", "CARBON_BENEFITS"
    target_role = Column(String(40), default="FARMER")
    content_json = Column(Text, nullable=False)
    duration_minutes = Column(Integer, default=5)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    completed = Column(Boolean, default=True)
    quiz_score = Column(Integer, default=100)
    certificate_issued = Column(Boolean, default=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class PartnerOffer(Base):
    __tablename__ = "partner_offers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    partner_name = Column(String(120), nullable=False)
    partner_category = Column(String(40), nullable=False)  # "INSURANCE", "CREDIT", "INPUTS", "EQUIPMENT"
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    price_paise = Column(BigInteger, default=0)
    status = Column(String(30), default="ACTIVE")
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    offer_id = Column(String(36), ForeignKey("partner_offers.id"), nullable=False)
    cooperative_id = Column(String(36), ForeignKey("cooperatives.id"), nullable=True)
    order_type = Column(String(40), default="GROUP_BUY")
    quantity = Column(Integer, default=1)
    total_amount_paise = Column(BigInteger, nullable=False)
    status = Column(String(30), default="CONFIRMED")
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class SchemeCatalogue(Base):
    __tablename__ = "scheme_catalogue"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    scheme_name = Column(String(160), nullable=False)
    level = Column(String(20), default="CENTRAL")  # "CENTRAL", "STATE"
    state = Column(String(60), nullable=True)
    description = Column(Text, nullable=False)
    eligibility_criteria_json = Column(Text, nullable=False)
    portal_url = Column(String(255), nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    category = Column(String(40), nullable=False)  # "TECHNICAL", "AGRONOMY", "PAYOUT", "GRIEVANCE"
    priority = Column(String(20), default="MEDIUM")
    subject = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN")  # "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"
    sla_deadline = Column(DateTime(timezone=True), nullable=False)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_sandbox = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False)
    author_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_type = Column(String(40), default="COMMENT")  # "COMMENT", "STATUS_CHANGE", "ESCALATION"
    notes = Column(Text, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    sender_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    receiver_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(36), nullable=False, index=True)
    body = Column(Text, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    template_name = Column(String(120), nullable=False)
    version = Column(String(30), default="V1.0")
    body_markdown = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class CreditNote(Base):
    __tablename__ = "credit_notes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    reason = Column(String(255), nullable=False)
    issued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    status = Column(String(30), default="PROCESSED")
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class Retirement(Base):
    __tablename__ = "retirements"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    contract_id = Column(String(36), ForeignKey("offtake_contracts.id"), nullable=False)
    buyer_org_id = Column(String(36), ForeignKey("organisations.id"), nullable=True)
    volume_tco2e = Column(Float, nullable=False)
    beneficiary_name = Column(String(120), nullable=False)
    reason = Column(String(255), nullable=False)
    serial_numbers_json = Column(Text, nullable=False)
    retired_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    retirement_id = Column(String(36), ForeignKey("retirements.id"), nullable=False)
    certificate_number = Column(String(60), unique=True, nullable=False)
    issued_to = Column(String(160), nullable=False)
    volume_tco2e = Column(Float, nullable=False)
    qr_code_svg = Column(Text, nullable=True)
    verification_hash = Column(String(64), nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id"), nullable=False)
    name = Column(String(80), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    scopes_json = Column(String(255), default='["registry:read"]')
    rate_limit_rpm = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id"), nullable=False)
    target_url = Column(String(255), nullable=False)
    events_json = Column(Text, default='["*"]')
    secret_key = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    endpoint_id = Column(String(36), ForeignKey("webhook_endpoints.id"), nullable=False)
    event_type = Column(String(60), nullable=False)
    payload_json = Column(Text, nullable=False)
    response_status = Column(Integer, default=200)
    attempts = Column(Integer, default=1)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class DataQualitySnapshot(Base):
    __tablename__ = "data_quality_snapshots"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    cooperative_id = Column(String(36), ForeignKey("cooperatives.id"), nullable=False)
    cloud_cover_pct = Column(Float, default=12.4)
    scene_gap_days = Column(Float, default=4.2)
    gps_accuracy_m = Column(Float, default=2.1)
    photo_pass_pct = Column(Float, default=94.5)
    reading_completeness_pct = Column(Float, default=96.2)
    snapshot_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    flag_key = Column(String(60), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    description = Column(String(255), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class VisitCheckin(Base):
    __tablename__ = "visit_checkins"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    agent_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plot_id = Column(String(36), ForeignKey("plots.id"), nullable=False)
    checkin_lat = Column(Float, nullable=False)
    checkin_lon = Column(Float, nullable=False)
    distance_to_centroid_m = Column(Float, default=15.0)
    checked_in_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)

class SampleCustodyEvent(Base):
    __tablename__ = "sample_custody_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    sample_id = Column(String(60), nullable=False)
    plot_id = Column(String(36), ForeignKey("plots.id"), nullable=False)
    handler_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    stage = Column(String(40), default="SAMPLE_COLLECTED")  # "SAMPLE_COLLECTED", "LAB_HANDOVER", "TESTED"
    notes = Column(Text, nullable=True)
    custody_hash = Column(String(64), nullable=False)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    disputed_entity_type = Column(String(40), nullable=False)  # "PLOT_AREA", "VERIFICATION_RESULT", "PAYOUT_AMOUNT"
    disputed_entity_id = Column(String(36), nullable=False)
    raised_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    dispute_reason = Column(Text, nullable=False)
    claimed_value = Column(String(100), nullable=True)
    status = Column(String(30), default="OPEN")  # "OPEN", "INVESTIGATING", "RESOLVED", "REJECTED"
    resolution_notes = Column(Text, nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(160), nullable=False)
    document_type = Column(String(40), nullable=False)  # "TERMS_OF_SERVICE", "BENEFIT_SHARING_AGREEMENT", "DPDP_PRIVACY_NOTICE"
    version_code = Column(String(30), nullable=False)
    content_markdown = Column(Text, nullable=False)
    counsel_approved = Column(Boolean, default=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

class LegalAcceptance(Base):
    __tablename__ = "legal_acceptances"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("legal_documents.id"), nullable=False)
    accepted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ip_address = Column(String(45), nullable=True)
    is_sandbox = Column(Boolean, default=False, nullable=False)

