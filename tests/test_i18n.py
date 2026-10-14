"""
i18n Quality Gate Pytest Suite.
Verifies Section 6 & Section 17 (Item 5):
- 100% key completeness across en, hi, te, ta, bn, qps-ploc
- Zero missing keys in any regional language
- Valid ICU syntax and balanced braces
- Pseudo-locale length expansion >= 25%
"""

from packages.i18n.verify_i18n import verify_all_locales

def test_i18n_locales_completeness():
    assert verify_all_locales() is True
