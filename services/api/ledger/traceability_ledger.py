"""
Append-Only Cryptographic SHA-256 Hash Chain with Batch Merkle Tree Engine.
Implements Section 2 (Item 7) & Section 6:
- Core architecture: An append-only Cryptographic SHA-256 Hash Chain linking blocks.
- Block integrity: Each block stores `index`, `entry_type`, `payload`, `timestamp`, `previous_hash`, and `entry_hash`.
- Batch Merkle Tree: When a block encapsulates multiple transactions (e.g. plot verification batch or payout batch),
  it computes a binary SHA-256 Merkle root over the leaf items and anchors `merkle_root` in the payload.
- Zero cryptocurrency, zero gas tokens, zero mining overhead.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def compute_merkle_root(leaf_items: List[Any]) -> str:
    """
    Computes standard binary SHA-256 Merkle Tree root for a list of items.
    If empty, returns 64 zeroes.
    If single item, returns hash of that item.
    Iteratively pairs and hashes adjacent nodes until the single root is reached.
    """
    if not leaf_items:
        return GENESIS_HASH

    current_level = [
        sha256_hex(json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item))
        for item in leaf_items
    ]

    while len(current_level) > 1:
        # If odd number of nodes, duplicate the last node
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])

        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            next_level.append(sha256_hex(combined))
        current_level = next_level

    return current_level[0]

class LedgerEntry:
    def __init__(
        self,
        index: int,
        entry_type: str,
        payload: Dict[str, Any],
        timestamp: float,
        previous_hash: str,
        merkle_root: Optional[str] = None
    ):
        self.index = index
        self.entry_type = entry_type
        self.payload = payload
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.merkle_root = merkle_root
        self.entry_hash = self.compute_hash()

    def compute_hash(self) -> str:
        serialized = json.dumps({
            "index": self.index,
            "entry_type": self.entry_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root
        }, sort_keys=True)
        return sha256_hex(serialized)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "entry_type": self.entry_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "entry_hash": self.entry_hash
        }

class TraceabilityLedger:
    def __init__(self):
        self.entries: List[LedgerEntry] = []
        # Create Genesis Block
        genesis = LedgerEntry(
            index=0,
            entry_type="GENESIS",
            payload={
                "message": "CarbonKheti Cryptographic Traceability Ledger Initialized",
                "standard": "Verra VM0051 v1.0",
                "architecture": "SHA-256 Hash Chain with Merkle Tree Batch Commit"
            },
            timestamp=1704067200.0,
            previous_hash=GENESIS_HASH,
            merkle_root=None
        )
        self.entries.append(genesis)

    @property
    def latest_entry(self) -> LedgerEntry:
        return self.entries[-1]

    def append_record(
        self,
        entry_type: str,
        payload: Dict[str, Any],
        sub_items: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Appends an event to the tamper-evident hash chain.
        If `sub_items` are provided, computes a binary Merkle Root over them.
        """
        prev = self.latest_entry
        merkle_root = compute_merkle_root(sub_items) if sub_items else None
        
        # If merkle_root is present, also store it in payload for quick indexing
        if merkle_root and "merkle_root" not in payload:
            payload = dict(payload)
            payload["merkle_root"] = merkle_root
            payload["leaf_count"] = len(sub_items) if sub_items else 0

        new_entry = LedgerEntry(
            index=len(self.entries),
            entry_type=entry_type,
            payload=payload,
            timestamp=time.time(),
            previous_hash=prev.entry_hash,
            merkle_root=merkle_root
        )
        self.entries.append(new_entry)
        return new_entry.to_dict()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Validates entire hash chain. Returns validation report and any compromised block.
        """
        for i in range(1, len(self.entries)):
            curr = self.entries[i]
            prev = self.entries[i - 1]

            if curr.previous_hash != prev.entry_hash:
                return {
                    "is_valid": False,
                    "compromised_index": i,
                    "reason": f"Hash chain break at block {i}: previous_hash does not match parent entry_hash"
                }

            if curr.compute_hash() != curr.entry_hash:
                return {
                    "is_valid": False,
                    "compromised_index": i,
                    "reason": f"Payload altered at block {i}: entry_hash mismatch"
                }

        return {
            "is_valid": True,
            "total_blocks": len(self.entries),
            "head_hash": self.latest_entry.entry_hash,
            "architecture": "Cryptographic SHA-256 Hash Chain with Merkle Batch Support",
            "status": "CHAIN_INTEGRITY_VERIFIED"
        }

    def get_entries_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.entries if e.entry_type == entry_type]

traceability_ledger = TraceabilityLedger()
