import os

# Superset requires a stable secret key for sessions/CSRF
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me")

# This is fine for local/demo. Production hardening is not required here.
WTF_CSRF_ENABLED = True

# Optional: if you run behind proxies later, you can adjust these.
# ENABLE_PROXY_FIX = True

