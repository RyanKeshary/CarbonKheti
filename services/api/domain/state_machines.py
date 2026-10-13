"""
CarbonKheti Domain State Machines.
Strictly implements Section 6 transitions:
- Season Enrolment State Machine
- Batch State Machine
- Offtake Contract State Machine
- Payout State Machine
- Grievance State Machine
"""

from typing import Set, Dict, List

# 1. Season Lifecycle
SEASON_STATES: Set[str] = {
    "ENROLLED",
    "BASELINE_DOCUMENTED",
    "MONITORING",
    "MID_SEASON_VERIFIED",
    "HARVESTED",
    "POST_HARVEST_VERIFIED",
    "AUDITED",
    "INCLUDED_IN_BATCH",
    "FLAGGED",
    "DROPPED_OUT",
    "ON_HOLD"
}

SEASON_ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "ENROLLED": ["BASELINE_DOCUMENTED", "DROPPED_OUT", "ON_HOLD"],
    "BASELINE_DOCUMENTED": ["MONITORING", "FLAGGED", "DROPPED_OUT", "ON_HOLD"],
    "MONITORING": ["MID_SEASON_VERIFIED", "FLAGGED", "DROPPED_OUT", "ON_HOLD"],
    "MID_SEASON_VERIFIED": ["HARVESTED", "FLAGGED", "DROPPED_OUT", "ON_HOLD"],
    "HARVESTED": ["POST_HARVEST_VERIFIED", "FLAGGED", "DROPPED_OUT"],
    "POST_HARVEST_VERIFIED": ["AUDITED", "FLAGGED"],
    "AUDITED": ["INCLUDED_IN_BATCH", "FLAGGED"],
    "INCLUDED_IN_BATCH": [],
    "FLAGGED": ["MONITORING", "DROPPED_OUT", "ON_HOLD"],
    "ON_HOLD": ["MONITORING", "DROPPED_OUT"],
    "DROPPED_OUT": []
}

# 2. Batch Lifecycle
BATCH_STATES: Set[str] = {
    "DRAFT",
    "ENROLLING",
    "VERIFIED_PRACTICE",
    "SUBMITTED_TO_VVB",
    "VVB_FINDINGS_OPEN",
    "VERIFIED",
    "REGISTRY_SUBMITTED",
    "ISSUED",
    "RETIRED"
}

BATCH_ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["ENROLLING"],
    "ENROLLING": ["VERIFIED_PRACTICE"],
    "VERIFIED_PRACTICE": ["SUBMITTED_TO_VVB"],
    "SUBMITTED_TO_VVB": ["VVB_FINDINGS_OPEN", "VERIFIED"],
    "VVB_FINDINGS_OPEN": ["VERIFIED", "SUBMITTED_TO_VVB"],
    "VERIFIED": ["REGISTRY_SUBMITTED"],
    "REGISTRY_SUBMITTED": ["ISSUED"],
    "ISSUED": ["RETIRED"],
    "RETIRED": []
}

# 3. Offtake Contract Lifecycle
CONTRACT_STATES: Set[str] = {
    "DRAFT",
    "SENT",
    "SIGNED",
    "INVOICED",
    "FUNDED",
    "FULFILLING",
    "DELIVERED",
    "CLOSED",
    "CANCELLED",
    "DISPUTED"
}

CONTRACT_ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["SENT", "CANCELLED"],
    "SENT": ["SIGNED", "CANCELLED"],
    "SIGNED": ["INVOICED", "CANCELLED"],
    "INVOICED": ["FUNDED", "CANCELLED"],
    "FUNDED": ["FULFILLING", "DISPUTED"],
    "FULFILLING": ["DELIVERED", "DISPUTED"],
    "DELIVERED": ["CLOSED", "DISPUTED"],
    "DISPUTED": ["FULFILLING", "CANCELLED", "CLOSED"],
    "CANCELLED": [],
    "CLOSED": []
}

# 4. Payout Lifecycle
PAYOUT_STATES: Set[str] = {
    "SCHEDULED",
    "AWAITING_APPROVAL",
    "APPROVED",
    "PROCESSING",
    "PAID",
    "FAILED",
    "RETRYING",
    "RETURNED"
}

PAYOUT_ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "SCHEDULED": ["AWAITING_APPROVAL", "FAILED"],
    "AWAITING_APPROVAL": ["APPROVED", "FAILED"],
    "APPROVED": ["PROCESSING", "FAILED"],
    "PROCESSING": ["PAID", "FAILED"],
    "FAILED": ["RETRYING", "RETURNED"],
    "RETRYING": ["PROCESSING", "FAILED"],
    "PAID": [],
    "RETURNED": []
}

# 5. Grievance Lifecycle
GRIEVANCE_STATES: Set[str] = {
    "OPEN",
    "ACKNOWLEDGED",
    "INVESTIGATING",
    "RESOLVED",
    "CLOSED"
}

GRIEVANCE_ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN": ["ACKNOWLEDGED"],
    "ACKNOWLEDGED": ["INVESTIGATING"],
    "INVESTIGATING": ["RESOLVED"],
    "RESOLVED": ["CLOSED", "INVESTIGATING"],
    "CLOSED": []
}

def validate_transition(current_state: str, next_state: str, transitions: Dict[str, List[str]], name: str) -> bool:
    allowed = transitions.get(current_state, [])
    if next_state not in allowed:
        raise ValueError(
            f"Invalid {name} transition: cannot move from '{current_state}' to '{next_state}'. "
            f"Allowed next states: {allowed}"
        )
    return True
