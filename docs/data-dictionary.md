# CarbonKheti Database Data Dictionary

This document details every table, foreign key relationship, and column constraint in the CarbonKheti PostgreSQL 16 + PostGIS / SQLite schema.

---

## 1. `users`
Core user identity and authentication credentials.
- `id` (VARCHAR(36), PK): UUID primary key.
- `phone_number` (VARCHAR(20), UNIQUE, INDEX): 10-digit Indian mobile number for OTP login.
- `full_name` (VARCHAR(120)): Real legal name.
- `role` (VARCHAR(30)): Role enum (`FARMER`, `COOPERATIVE_AGENT`, `FACTORY_BUYER`, `AUDITOR`, `ADMIN`).
- `language_pref` (VARCHAR(10)): Language code (`en`, `te`, `hi`, `ta`, etc.).
- `state`, `district` (VARCHAR(60)): Location references.
- `created_at` (FLOAT): Epoch timestamp.

## 2. `cooperatives`
Farmer Producer Organisations (FPOs) and primary agricultural societies.
- `id` (VARCHAR(36), PK): Cooperative UUID.
- `name` (VARCHAR(160)): Registered society name.
- `registration_number` (VARCHAR(80), UNIQUE): State cooperative society registration code.
- `state`, `district` (VARCHAR(60)): Operational jurisdiction.
- `bank_account_masked` (VARCHAR(40)): Verified bank account reference for 15% cooperative facilitation payouts.
- `is_verified` (BOOLEAN): Status of KYC and registration documentation.

## 3. `farmers`
Smallholder farmer participants.
- `id` (VARCHAR(36), PK): Participant code (e.g. `F-RAMESH`).
- `user_id` (VARCHAR(36), FK -> `users.id`): Linked user identity.
- `cooperative_id` (VARCHAR(36), FK -> `cooperatives.id`): Member cooperative.
- `agristack_id` (VARCHAR(60)): National AgriStack Farmer ID where provisioned.
- `state_land_record_no` (VARCHAR(80)): Survey number or RoR extract number.
- `bank_account_masked`, `upi_id` (VARCHAR): Direct payout destination.
- `is_tenant` (BOOLEAN): Indicates tenant operating farmer.
- `landlord_consent_hash` (VARCHAR(64)): SHA-256 hash of signed landowner agreement.
- `dpdp_consent_granted` (BOOLEAN): DPDP Act 2023 explicit consent record.
- `dpdp_consent_timestamp` (FLOAT): Timestamp of consent signing.

## 4. `plots`
Agricultural land parcels.
- `id` (VARCHAR(36), PK): Plot parcel code (e.g. `PL-NALGONDA-01`).
- `farmer_id` (VARCHAR(36), FK -> `farmers.id`): Land operator.
- `plot_name` (VARCHAR(100)): Survey number or informal field name.
- `area_ha` (FLOAT): Accurate geodesic area in hectares (calculated via EPSG:6933).
- `boundary_geojson` (TEXT): GeoJSON Polygon boundary coordinates.
- `centroid_lat`, `centroid_lon` (FLOAT): Geographic centroid coordinates.
- `baseline_water_regime` (VARCHAR(40)): Documented historical practice (`CONTINUOUS_FLOODING`).
- `baseline_years_documented` (INTEGER): Number of documented prior seasons ($\ge 3$).

## 5. `season_enrolments`
Specific crop seasons for a plot.
- `id` (VARCHAR(36), PK): Season code (e.g. `SN-KHARIF-2026-01`).
- `plot_id` (VARCHAR(36), FK -> `plots.id`): Enrolled plot.
- `season_code` (VARCHAR(30)): `KHARIF_2026`, `RABI_2026`.
- `practice_code` (VARCHAR(30)): `AWD_SAFE`, `DSR_DRILL`.
- `status` (VARCHAR(40)): `ENROLLED`, `MONITORING`, `MID_SEASON_VERIFIED`, `HARVESTED`, `AUDITED`.

## 6. `evidence_records`
Auditable field evidence entries.
- `id` (VARCHAR(36), PK): Evidence item ID.
- `season_id` (VARCHAR(36), FK -> `season_enrolments.id`): Crop season.
- `evidence_type` (VARCHAR(30)): `PHOTO`, `TUBE_READING`, `SENTINEL_1`, `SENTINEL_2`, `FIRMS_FIRE`.
- `data_payload_json` (TEXT): Structured JSON of readings, backscatter, or NDVI curves.
- `sha256_hash` (VARCHAR(64)): Cryptographic payload checksum.
- `phash` (VARCHAR(32)): Perceptual image hash.
- `blur_score` (FLOAT): Laplacian blur variance.
- `quality_status` (VARCHAR(30)): `PASSED`, `FLAGGED_FOR_AUDITOR_REVIEW`.

## 7. `mrv_calculations`
Deterministic Verra VM0051 v1.0 calculation outputs.
- `id` (VARCHAR(36), PK): Calculation record ID.
- `season_id` (VARCHAR(36), FK -> `season_enrolments.id`, UNIQUE): 1:1 relation.
- `methodology_version` (VARCHAR(30)): `VM0051 v1.0`.
- `baseline_ch4_kg`, `project_ch4_kg` (FLOAT): Seasonal emissions in kg CH4.
- `gross_reduction_tco2e` (FLOAT): Gross reductions before deductions.
- `uncertainty_discount_tco2e` (FLOAT): Deduction for baseline error propagation.
- `buffer_deduction_tco2e` (FLOAT): 10% deduction for Verra pooled buffer account.
- `net_creditable_point` (FLOAT): Net creditable tonnes CO2e.
- `net_creditable_min`, `net_creditable_max` (FLOAT): 95% confidence interval bounds.
- `water_saved_m3` (FLOAT): Estimated cubic meters of irrigation water saved.
- `audit_trail_json` (TEXT): Complete formula audit trail and IPCC citations.

## 8. `project_batches`
Aggregated regional project batches.
- `id` (VARCHAR(36), PK): Batch code (e.g. `CK-VCS-VM0051-TS-01`).
- `region` (VARCHAR(100)): State and districts.
- `vintage_year` (INTEGER): Crop year (e.g. 2026).
- `estimated_volume_tco2e` (FLOAT): Estimated total volume.
- `uncertainty_min_tco2e`, `uncertainty_max_tco2e` (FLOAT): Batch uncertainty bounds.
- `price_per_tco2e_inr` (INTEGER): Agreed reference or clearing price.
- `status` (VARCHAR(40)): `ENROLLED`, `VERIFIED_PRACTICE`, `PRE_ISSUANCE_OFFTAKE`, `ISSUED`.
- `registry_serial_range` (VARCHAR(120), NULLABLE): Real Verra serial numbers once issued.

## 9. `offtake_contracts`
Industrial buyer pre-issuance offtake agreements.
- `id` (VARCHAR(36), PK): Contract ID.
- `factory_id` (VARCHAR(36), FK -> `users.id`): Purchasing corporate entity.
- `batch_id` (VARCHAR(36), FK -> `project_batches.id`): Sourced batch.
- `requested_tco2e` (FLOAT): Offtake volume.
- `price_per_tonne_inr` (INTEGER): Agreed price per tonne.
- `total_amount_paise` (BIGINT): Total amount in integer paise.
- `contract_status` (VARCHAR(40)): `PRE_ISSUANCE_AGREEMENT`, `EXECUTED`.

## 10. `payouts`
Staged direct disbursements to farmers.
- `id` (VARCHAR(36), PK): Payout record ID.
- `farmer_id` (VARCHAR(36), FK -> `farmers.id`): Recipient.
- `season_id` (VARCHAR(36), FK -> `season_enrolments.id`): Verified season.
- `stage` (VARCHAR(30)): `STAGE_1_MID_SEASON` (30%) or `STAGE_2_HARVEST` (70%).
- `amount_paise` (BIGINT): Strictly integer paise (NEVER floating point).
- `status` (VARCHAR(40)): `SCHEDULED`, `PROCESSING`, `PAID`, `FAILED`.
- `utr_reference` (VARCHAR(60)): Banking UTR transaction reference number.
- `idempotency_key` (VARCHAR(64), UNIQUE): Unique deduplication key.
