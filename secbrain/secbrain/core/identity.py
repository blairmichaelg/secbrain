"""Identity and session abstractions for multi-context testing.

This module provides identity management for security testing including:
- Multiple identity contexts (attacker, victim, admin, etc.)
- Session state management (headers, cookies, tokens)
- Identity registry for tracking multiple sessions
- Request context switching
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IdentitySession:
    """Represents an identity (attacker/victim/etc) with headers, cookies, and tokens."""

    name: str
    role: str = "attacker"
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    tokens: dict[str, Any] = field(default_factory=dict)

    def with_header(self, key: str, value: str) -> IdentitySession:
        self.headers[key] = value
        return self

    def with_cookie(self, key: str, value: str) -> IdentitySession:
        self.cookies[key] = value
        return self

    def set_token(self, key: str, value: Any) -> None:
        self.tokens[key] = value

    def get_token(self, key: str) -> Any | None:
        return self.tokens.get(key)

    def apply(self, headers: dict[str, str] | None = None, cookies: dict[str, str] | None = None) -> tuple[dict[str, str], dict[str, str]]:
        """Merge identity headers/cookies onto provided dictionaries without mutating inputs."""
        merged_headers = {**(headers or {}), **self.headers}
        merged_cookies = {**(cookies or {}), **self.cookies}
        return merged_headers, merged_cookies


class IdentityRegistry:
    """Registry for multiple identities within a run (attacker, victim, etc.)."""

    def __init__(self) -> None:
        self._identities: dict[str, IdentitySession] = {}
        self.active: str | None = None

    def register(self, identity: IdentitySession) -> None:
        self._identities[identity.name] = identity
        if self.active is None:
            self.active = identity.name

    def get(self, name: str | None = None) -> IdentitySession:
        """Get an identity by name.
        
        Args:
            name: Identity name to retrieve. If None, returns the active identity.
            
        Returns:
            The requested IdentitySession
            
        Raises:
            KeyError: If the identity is not registered
            ValueError: If name is None and no active identity is set
        """
        target = name or self.active
        if target is None:
            raise ValueError("No active identity set and no name provided")
        if target not in self._identities:
            available = ", ".join(self._identities.keys()) if self._identities else "none"
            raise KeyError(
                f"Identity '{target}' not registered. Available identities: {available}"
            )
        return self._identities[target]

    def switch(self, name: str) -> IdentitySession:
        """Switch to a different identity.
        
        Args:
            name: Name of the identity to switch to
            
        Returns:
            The newly active IdentitySession
            
        Raises:
            KeyError: If the identity is not registered
        """
        if name not in self._identities:
            available = ", ".join(self._identities.keys()) if self._identities else "none"
            raise KeyError(
                f"Cannot switch to '{name}': not registered. Available: {available}"
            )
        self.active = name
        return self.get(name)

    def list_identities(self) -> list[str]:
        return list(self._identities.keys())
