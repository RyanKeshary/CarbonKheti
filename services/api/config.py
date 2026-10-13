"""
CarbonKheti Configuration & Environment Integrity Guard.
Strictly implements Section 1:
- APP_ENV: 'production' | 'sandbox'
- Server crashes on boot if sandbox features (SANDBOX_AUTH, SANDBOX_PAY) are enabled in production!
"""

import os
import sys

APP_ENV = os.getenv("APP_ENV", "sandbox").lower()

# Sandbox switches
SANDBOX_AUTH = os.getenv("SANDBOX_AUTH", "true").lower() in ("true", "1", "yes") if APP_ENV == "sandbox" else False
SANDBOX_PAY = os.getenv("SANDBOX_PAY", "true").lower() in ("true", "1", "yes") if APP_ENV == "sandbox" else False

# Hard integrity crash guard:
if APP_ENV == "production":
    raw_sbx_auth = os.getenv("SANDBOX_AUTH", "").lower() in ("true", "1", "yes")
    raw_sbx_pay = os.getenv("SANDBOX_PAY", "").lower() in ("true", "1", "yes")
    if raw_sbx_auth or raw_sbx_pay:
        error_msg = (
            "FATAL INTEGRITY VIOLATION (Rule 0): "
            "Server refuses to boot because SANDBOX_AUTH or SANDBOX_PAY is enabled in APP_ENV=production! "
            "Sandbox features must never operate in production mode."
        )
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

IS_SANDBOX = (APP_ENV == "sandbox")
JWT_SECRET = os.getenv("JWT_SECRET", "carbonkheti_dev_jwt_secret_change_in_prod_2026")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/carbonkheti.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Bank UTR vs Sandbox Prefix
TXN_ID_PREFIX = "SBX-" if IS_SANDBOX else "CK-"
