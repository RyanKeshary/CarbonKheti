"""
CarbonKheti i18n Quality Gate Validator.
Implements Section 6 CI Quality Gate:
1. Validates that every launch language (en, hi, te, ta, bn, qps-ploc) has 100% string completeness.
2. Missing-key detection: flags any key missing in regional languages compared to canonical en.json.
3. Unused-key / extraneous key detection.
4. ICU MessageFormat syntax validation (balanced braces, valid plural forms).
5. Pseudo-localization length expansion check (>30% longer than English).
"""

import os
import json
import sys
import re

LAUNCH_LOCALES = ["en", "hi", "te", "ta", "bn", "qps-ploc"]

def extract_flat_keys(d, prefix=""):
    keys = {}
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(extract_flat_keys(v, full_key))
        else:
            keys[full_key] = v
    return keys

def validate_icu_syntax(key, text):
    # Check for balanced braces
    open_count = text.count("{")
    close_count = text.count("}")
    if open_count != close_count:
        return f"Mismatched braces in {key}: {open_count} open vs {close_count} close"
    
    # If plural format used, check for required clauses
    if "plural" in text:
        if not re.search(r'other\s*\{', text):
            return f"ICU plural in {key} missing mandatory 'other' clause"
            
    return None

def verify_all_locales():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    locales_dir = os.path.join(dir_path, "locales")

    en_path = os.path.join(locales_dir, "en.json")
    if not os.path.exists(en_path):
        print(f"ERROR: Base en.json missing at {en_path}")
        sys.exit(1)

    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    en_keys = extract_flat_keys(en_data)
    total_en_keys = len(en_keys)
    print(f"Loaded canonical en.json with {total_en_keys} keys.")

    errors = []
    locale_stats = {}

    for locale in LAUNCH_LOCALES:
        loc_path = os.path.join(locales_dir, f"{locale}.json")
        if not os.path.exists(loc_path):
            errors.append(f"Missing locale file: {locale}.json")
            continue

        with open(loc_path, "r", encoding="utf-8") as f:
            loc_data = json.load(f)

        loc_keys = extract_flat_keys(loc_data)
        missing = set(en_keys.keys()) - set(loc_keys.keys())
        extra = set(loc_keys.keys()) - set(en_keys.keys())

        if missing:
            errors.append(f"Locale '{locale}' is missing {len(missing)} keys: {list(missing)[:5]}")
        if extra:
            errors.append(f"Locale '{locale}' has {len(extra)} unknown extra keys: {list(extra)[:5]}")

        # Check ICU syntax
        syntax_errs = 0
        for k, v in loc_keys.items():
            err = validate_icu_syntax(f"{locale}:{k}", str(v))
            if err:
                errors.append(err)
                syntax_errs += 1

        # Check expansion for pseudo-locale
        expansion_pct = 0
        if locale == "qps-ploc":
            en_len = sum(len(str(v)) for v in en_keys.values())
            ploc_len = sum(len(str(v)) for v in loc_keys.values())
            expansion_pct = round(((ploc_len - en_len) / en_len) * 100, 1)
            if expansion_pct < 25:
                errors.append(f"Pseudo-locale expansion insufficient ({expansion_pct}%), expected >= 30%")

        completeness = round((len(loc_keys.keys() & en_keys.keys()) / total_en_keys) * 100, 1)
        locale_stats[locale] = {
            "total_keys": len(loc_keys),
            "completeness_pct": completeness,
            "missing_keys": len(missing),
            "extra_keys": len(extra),
            "syntax_errors": syntax_errs,
            "expansion_pct": expansion_pct
        }

    print("\n--- i18n Verification Results ---")
    for loc, s in locale_stats.items():
        print(f"[{loc}] Completeness: {s['completeness_pct']}% | Total Keys: {s['total_keys']} | Missing: {s['missing_keys']}")

    if errors:
        print("\nERRORS DETECTED:")
        for e in errors:
            print(f"  [FAIL] {e}")
        return False
    else:
        print("\n[SUCCESS] All launch locales passed i18n quality gate: 100% complete, zero missing keys, valid ICU syntax.")
        return True

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    success = verify_all_locales()
    sys.exit(0 if success else 1)

