"""
Cryptographic Traceability Ledger & Merkle Tree Test Suite.
Verifies Section 2 (Item 7) & Section 15:
- Validates SHA-256 block linking (previous_hash == parent.entry_hash)
- Validates binary Merkle tree root calculation over batch sub-items
- Validates detection of tampered blocks
"""

from services.api.ledger.traceability_ledger import TraceabilityLedger, compute_merkle_root

def test_merkle_root_computation():
    leaves = [
        {"plot_id": "P1", "area": 1.08},
        {"plot_id": "P2", "area": 0.95},
        {"plot_id": "P3", "area": 1.40}
    ]
    root1 = compute_merkle_root(leaves)
    assert len(root1) == 64  # Valid SHA-256 hex string

    # Determinism
    root2 = compute_merkle_root(leaves)
    assert root1 == root2

    # Sensitivity: altering any leaf alters the root
    leaves_altered = [
        {"plot_id": "P1", "area": 1.09},  # Altered area
        {"plot_id": "P2", "area": 0.95},
        {"plot_id": "P3", "area": 1.40}
    ]
    root_altered = compute_merkle_root(leaves_altered)
    assert root1 != root_altered

def test_hash_chain_integrity_and_tamper_detection():
    ledger = TraceabilityLedger()
    assert len(ledger.entries) == 1  # Genesis block

    # Append block 1
    b1 = ledger.append_record(
        entry_type="PLOT_ENROLLED",
        payload={"plot_id": "SBX-PLT-001", "area_ha": 1.08}
    )
    assert b1["index"] == 1
    assert b1["previous_hash"] == ledger.entries[0].entry_hash

    # Append block 2 with composite sub-items (Merkle root)
    b2 = ledger.append_record(
        entry_type="PAYOUT_BATCH_COMMITTED",
        payload={"batch_id": "SBX-POB-01", "total_paise": 180672},
        sub_items=[{"payout_id": "PO1", "amount": 126470}, {"payout_id": "PO2", "amount": 27101}]
    )
    assert b2["index"] == 2
    assert b2["previous_hash"] == ledger.entries[1].entry_hash
    assert "merkle_root" in b2
    assert len(b2["merkle_root"]) == 64

    # Verify chain integrity
    report = ledger.verify_chain_integrity()
    assert report["is_valid"] is True
    assert report["total_blocks"] == 3

    # Tampering test: modify payload in block 1
    ledger.entries[1].payload["area_ha"] = 999.0
    tampered_report = ledger.verify_chain_integrity()
    assert tampered_report["is_valid"] is False
    assert tampered_report["compromised_index"] == 1
