"""
Append-Only Cryptographic Hash-Chained Traceability Ledger.
Complies with Section 6:
Links: Plot -> Season Evidence -> Verified Area -> Estimated/Issued Credits -> Buyer Contracts -> Payouts.
Each entry is hash-chained (SHA-256).
Provides tamper verification and auditable history.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class LedgerEntry:
    def __init__(
        self,
        index: int,
        entry_type: str,
        payload: Dict[str, Any],
        timestamp: float,
        previous_hash: str
    ):
        self.index = index
        self.entry_type = entry_type
        self.payload = payload
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.entry_hash = self.compute_hash()

    def compute_hash(self) -> str:
        serialized = json.dumps({
            "index": self.index,
            "entry_type": self.entry_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "entry_type": self.entry_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash
        }

class TraceabilityLedger:
    def __init__(self):
        self.entries: List[LedgerEntry] = []
        # Create Genesis Entry
        genesis = LedgerEntry(
            index=0,
            entry_type="GENESIS",
            payload={"message": "CarbonKheti Traceability Ledger Initialized", "standard": "Verra VM0051 v1.0"},
            timestamp=1704067200.0,
            previous_hash=GENESIS_HASH
        )
        self.entries.append(genesis)

    @property
    def latest_entry(self) -> LedgerEntry:
        return self.entries[-1]

    def append_record(self, entry_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Appends a verified event to the tamper-evident hash chain.
        Entry types:
        - PLOT_ENROLLED
        - EVIDENCE_VERIFIED
        - MRV_CALCULATION_SEALED
        - BATCH_CREATED
        - REGISTRY_ISSUANCE_RECORDED
        - OFFTAKE_ALLOCATED
        - PAYOUT_TRANCHE_COMMITTED
        """
        prev = self.latest_entry
        new_entry = LedgerEntry(
            index=len(self.entries),
            entry_type=entry_type,
            payload=payload,
            timestamp=time.time(),
            previous_hash=prev.entry_hash
        )
        self.entries.append(new_entry)
        return new_entry.to_dict()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Validates entire hash chain. Returns valid boolean and any compromised index.
        """
        for i in range(1, len(self.entries)):
            curr = self.entries[i]
            prev = self.entries[i - 1]

            if curr.previous_hash != prev.entry_hash:
                return {
                    "is_valid": False,
                    "compromised_index": i,
                    "reason": f"Hash break at entry {i}: previous_hash does not match parent entry_hash"
                }

            if curr.compute_hash() != curr.entry_hash:
                return {
                    "is_valid": False,
                    "compromised_index": i,
                    "reason": f"Payload altered at entry {i}: entry_hash mismatch"
                }

        return {
            "is_valid": True,
            "total_blocks": len(self.entries),
            "head_hash": self.latest_entry.entry_hash,
            "status": "CHAIN_INTEGRITY_VERIFIED"
        }

    def get_entries_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.entries if e.entry_type == entry_type]

traceability_ledger = TraceabilityLedger()
