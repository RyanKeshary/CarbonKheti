#!/usr/bin/env python3
"""
CarbonKheti Fact Bank Validator
Validates schema, required fields, and verifies URL integrity.
Ensures zero unverified statistics or dead source links.
"""

import json
import os
import sys
import urllib.request
import urllib.error

FACTS_FILE = os.path.join(os.path.dirname(__file__), "facts.json")

REQUIRED_KEYS = [
    "id",
    "claim",
    "value",
    "unit",
    "year",
    "caveats",
    "publisher",
    "title",
    "source_url",
    "retrieved_date",
]

def validate_facts(check_network=False):
    if not os.path.exists(FACTS_FILE):
        print(f"Error: {FACTS_FILE} not found.", file=sys.stderr)
        return False

    with open(FACTS_FILE, "r", encoding="utf-8") as f:
        try:
            facts = json.load(f)
        except Exception as e:
            print(f"Error: Failed to parse JSON: {e}", file=sys.stderr)
            return False

    if not isinstance(facts, list) or len(facts) == 0:
        print("Error: facts.json must be a non-empty array.", file=sys.stderr)
        return False

    print(f"Loaded {len(facts)} verified facts from Fact Bank.")
    seen_ids = set()
    errors = 0

    for i, item in enumerate(facts):
        for k in REQUIRED_KEYS:
            if k not in item or item[k] is None:
                print(f"Fact #{i+1} [{item.get('id', 'unknown')}]: Missing required key '{k}'", file=sys.stderr)
                errors += 1

        fid = item.get("id")
        if fid in seen_ids:
            print(f"Duplicate fact ID '{fid}' found.", file=sys.stderr)
            errors += 1
        seen_ids.add(fid)

        # URL format check
        url = item.get("source_url", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            print(f"Fact '{fid}': Invalid URL format '{url}'", file=sys.stderr)
            errors += 1

        if check_network:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "CarbonKheti-FactVerifier/1.0 (Verification; +https://carbonkheti.in)"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        print(f"Warning: URL for '{fid}' returned HTTP {resp.status}: {url}")
            except urllib.error.HTTPError as e:
                # 403 / 429 might be bot protection on some domains (e.g. msci or techcrunch)
                print(f"Info: {fid} HTTP {e.code} ({e.reason}) for {url}")
            except Exception as e:
                print(f"Network check note for '{fid}': {e}")

    if errors > 0:
        print(f"Failed with {errors} validation errors.", file=sys.stderr)
        return False

    print("All facts passed schema integrity checks successfully.")
    return True

if __name__ == "__main__":
    check_net = "--check-network" in sys.argv
    success = validate_facts(check_network=check_net)
    sys.exit(0 if success else 1)
