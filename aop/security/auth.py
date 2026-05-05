"""Authentication and authorization primitives.

  • APITokenAuthenticator: opaque bearer tokens scoped to a tenant
  • JWTAuthenticator: validates JWTs with JWK fetcher / shared secret
  • Role / require_role: minimal RBAC enforcement
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class Role(str, Enum):
    ADMIN = "admin"
    DEV = "dev"
    VIEWER = "viewer"


_ROLE_RANK = {Role.VIEWER: 1, Role.DEV: 2, Role.ADMIN: 3}


def role_meets(required: Role, granted: Role) -> bool:
    return _ROLE_RANK.get(granted, 0) >= _ROLE_RANK.get(required, 0)


# ---------------------------------------------------------------------------
# API token auth
# ---------------------------------------------------------------------------

@dataclass
class APIToken:
    token: str
    tenant_id: str
    role: Role = Role.VIEWER
    label: Optional[str] = None


class APITokenAuthenticator:
    def __init__(self, tokens: Iterable[APIToken]) -> None:
        self._by_token: Dict[str, APIToken] = {t.token: t for t in tokens}

    def authenticate(self, header_value: str) -> Optional[APIToken]:
        if not header_value or not header_value.lower().startswith("bearer "):
            return None
        return self._by_token.get(header_value.split(" ", 1)[1])

    def add(self, token: APIToken) -> None:
        self._by_token[token.token] = token

    def revoke(self, token: str) -> None:
        self._by_token.pop(token, None)


# ---------------------------------------------------------------------------
# JWT auth (HS256 default; RS256 if cryptography available)
# ---------------------------------------------------------------------------

class JWTAuthenticator:
    def __init__(
        self,
        *,
        secret: Optional[bytes] = None,
        public_key_pem: Optional[bytes] = None,
        algorithms: Iterable[str] = ("HS256", "RS256"),
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        leeway_s: int = 30,
    ) -> None:
        try:
            import jwt  # type: ignore
        except ImportError as e:
            raise ImportError(
                "JWT auth requires PyJWT. Install with: pip install pyjwt"
            ) from e
        self._jwt = jwt
        self.secret = secret
        self.public_key = public_key_pem
        self.algorithms = list(algorithms)
        self.issuer = issuer
        self.audience = audience
        self.leeway = leeway_s

    def authenticate(self, header_value: str) -> Optional[Dict[str, Any]]:
        if not header_value or not header_value.lower().startswith("bearer "):
            return None
        token = header_value.split(" ", 1)[1]
        key = self.public_key or self.secret
        if not key:
            return None
        try:
            return self._jwt.decode(
                token, key=key, algorithms=self.algorithms,
                issuer=self.issuer, audience=self.audience,
                leeway=self.leeway,
            )
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def require_role(required: Role) -> Callable:
    """Decorator that enforces a minimum role on the principal in kwargs['principal']."""

    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            principal = kwargs.get("principal")
            granted = getattr(principal, "role", None)
            if granted is None or not role_meets(required, granted):
                raise PermissionError(f"role {granted} insufficient (need {required})")
            return fn(*args, **kwargs)
        return wrapper
    return deco
