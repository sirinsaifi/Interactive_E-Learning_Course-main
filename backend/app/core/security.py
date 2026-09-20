"""Simple session token helpers.

No JWT, no OAuth. A session token is a URL-safe random string generated
with Python's secrets module. Tokens are stored in the users table and
looked up on every authenticated request.
"""
from __future__ import annotations

import secrets


def generate_session_token() -> str:
    """Return a cryptographically secure 43-character URL-safe session token."""
    return secrets.token_urlsafe(32)
