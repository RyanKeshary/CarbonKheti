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
