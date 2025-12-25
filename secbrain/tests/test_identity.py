"""Tests for identity and session abstractions."""

import pytest

from secbrain.core.identity import IdentityRegistry, IdentitySession


class TestIdentitySession:
    """Test IdentitySession dataclass."""

    def test_basic_initialization(self) -> None:
        """Test basic IdentitySession initialization."""
        session = IdentitySession(name="attacker1")
        assert session.name == "attacker1"
        assert session.role == "attacker"
        assert session.headers == {}
        assert session.cookies == {}
        assert session.tokens == {}

    def test_initialization_with_role(self) -> None:
        """Test IdentitySession initialization with custom role."""
        session = IdentitySession(name="user1", role="victim")
        assert session.name == "user1"
        assert session.role == "victim"

    def test_initialization_with_all_fields(self) -> None:
        """Test IdentitySession initialization with all fields."""
        headers = {"Authorization": "Bearer token"}
        cookies = {"session": "abc123"}
        tokens = {"csrf": "xyz789"}

        session = IdentitySession(
            name="test_user",
            role="custom",
            headers=headers,
            cookies=cookies,
            tokens=tokens,
        )

        assert session.name == "test_user"
        assert session.role == "custom"
        assert session.headers == headers
        assert session.cookies == cookies
        assert session.tokens == tokens

    def test_with_header(self) -> None:
        """Test adding header to session."""
        session = IdentitySession(name="user1")
        result = session.with_header("Content-Type", "application/json")

        assert result is session  # Returns self for chaining
        assert session.headers["Content-Type"] == "application/json"

    def test_with_header_chaining(self) -> None:
        """Test chaining multiple header additions."""
        session = IdentitySession(name="user1")
        session.with_header("Accept", "text/html").with_header("User-Agent", "TestAgent")

        assert session.headers["Accept"] == "text/html"
        assert session.headers["User-Agent"] == "TestAgent"

    def test_with_cookie(self) -> None:
        """Test adding cookie to session."""
        session = IdentitySession(name="user1")
        result = session.with_cookie("sessionid", "123456")

        assert result is session  # Returns self for chaining
        assert session.cookies["sessionid"] == "123456"

    def test_with_cookie_chaining(self) -> None:
        """Test chaining multiple cookie additions."""
        session = IdentitySession(name="user1")
        session.with_cookie("sessionid", "123").with_cookie("csrftoken", "abc")

        assert session.cookies["sessionid"] == "123"
        assert session.cookies["csrftoken"] == "abc"

    def test_set_token(self) -> None:
        """Test setting token."""
        session = IdentitySession(name="user1")
        session.set_token("access_token", "token123")

        assert session.tokens["access_token"] == "token123"

    def test_set_token_multiple(self) -> None:
        """Test setting multiple tokens."""
        session = IdentitySession(name="user1")
        session.set_token("access", "access123")
        session.set_token("refresh", "refresh456")

        assert session.tokens["access"] == "access123"
        assert session.tokens["refresh"] == "refresh456"

    def test_get_token_existing(self) -> None:
        """Test getting existing token."""
        session = IdentitySession(name="user1")
        session.set_token("key", "value")

        assert session.get_token("key") == "value"

    def test_get_token_nonexistent(self) -> None:
        """Test getting nonexistent token returns None."""
        session = IdentitySession(name="user1")
        assert session.get_token("missing") is None

    def test_apply_empty(self) -> None:
        """Test apply with no existing headers/cookies."""
        session = IdentitySession(name="user1")
        session.with_header("X-Test", "value1")
        session.with_cookie("test", "cookie1")

        headers, cookies = session.apply()

        assert headers == {"X-Test": "value1"}
        assert cookies == {"test": "cookie1"}

    def test_apply_with_existing(self) -> None:
        """Test apply merging with existing headers/cookies."""
        session = IdentitySession(name="user1")
        session.with_header("X-Identity", "user1")
        session.with_cookie("id", "123")

        existing_headers = {"Content-Type": "application/json"}
        existing_cookies = {"sessionid": "abc"}

        headers, cookies = session.apply(existing_headers, existing_cookies)

        # Should have both existing and identity values
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Identity"] == "user1"
        assert cookies["sessionid"] == "abc"
        assert cookies["id"] == "123"

    def test_apply_override(self) -> None:
        """Test that identity values override existing values."""
        session = IdentitySession(name="user1")
        session.with_header("Accept", "text/html")
        session.with_cookie("sessionid", "new123")

        existing_headers = {"Accept": "application/json"}
        existing_cookies = {"sessionid": "old456"}

        headers, cookies = session.apply(existing_headers, existing_cookies)

        # Identity values should override
        assert headers["Accept"] == "text/html"
        assert cookies["sessionid"] == "new123"

    def test_apply_no_mutation(self) -> None:
        """Test that apply doesn't mutate input dictionaries."""
        session = IdentitySession(name="user1")
        session.with_header("X-New", "value")
        session.with_cookie("new", "cookie")

        original_headers = {"X-Old": "old"}
        original_cookies = {"old": "cookie"}

        session.apply(original_headers, original_cookies)

        # Original dictionaries should be unchanged
        assert original_headers == {"X-Old": "old"}
        assert original_cookies == {"old": "cookie"}


class TestIdentityRegistry:
    """Test IdentityRegistry class."""

    def test_initialization(self) -> None:
        """Test IdentityRegistry initialization."""
        registry = IdentityRegistry()
        assert registry._identities == {}
        assert registry.active is None

    def test_register_single_identity(self) -> None:
        """Test registering a single identity."""
        registry = IdentityRegistry()
        session = IdentitySession(name="attacker1")

        registry.register(session)

        assert "attacker1" in registry._identities
        assert registry.active == "attacker1"

    def test_register_multiple_identities(self) -> None:
        """Test registering multiple identities."""
        registry = IdentityRegistry()
        attacker = IdentitySession(name="attacker", role="attacker")
        victim = IdentitySession(name="victim", role="victim")

        registry.register(attacker)
        registry.register(victim)

        assert "attacker" in registry._identities
        assert "victim" in registry._identities

    def test_first_registered_becomes_active(self) -> None:
        """Test that first registered identity becomes active."""
        registry = IdentityRegistry()
        session1 = IdentitySession(name="first")
        session2 = IdentitySession(name="second")

        registry.register(session1)
        registry.register(session2)

        assert registry.active == "first"

    def test_get_by_name(self) -> None:
        """Test getting identity by name."""
        registry = IdentityRegistry()
        session = IdentitySession(name="test_user")
        registry.register(session)

        retrieved = registry.get("test_user")
        assert retrieved is session

    def test_get_active(self) -> None:
        """Test getting active identity without name."""
        registry = IdentityRegistry()
        session = IdentitySession(name="active_user")
        registry.register(session)

        retrieved = registry.get()
        assert retrieved is session

    def test_get_nonexistent_raises(self) -> None:
        """Test that getting nonexistent identity raises KeyError."""
        registry = IdentityRegistry()

        with pytest.raises(KeyError, match="Identity 'missing' not registered"):
            registry.get("missing")

    def test_get_when_no_active_raises(self) -> None:
        """Test that getting without active identity raises KeyError."""
        registry = IdentityRegistry()

        with pytest.raises(KeyError):
            registry.get()

    def test_switch(self) -> None:
        """Test switching active identity."""
        registry = IdentityRegistry()
        session1 = IdentitySession(name="user1")
        session2 = IdentitySession(name="user2")

        registry.register(session1)
        registry.register(session2)

        assert registry.active == "user1"

        result = registry.switch("user2")
        assert registry.active == "user2"
        assert result is session2

    def test_switch_returns_session(self) -> None:
        """Test that switch returns the switched-to session."""
        registry = IdentityRegistry()
        session = IdentitySession(name="target")
        registry.register(session)

        result = registry.switch("target")
        assert result is session

    def test_list_identities_empty(self) -> None:
        """Test listing identities when registry is empty."""
        registry = IdentityRegistry()
        assert registry.list_identities() == []

    def test_list_identities_single(self) -> None:
        """Test listing identities with single identity."""
        registry = IdentityRegistry()
        session = IdentitySession(name="user1")
        registry.register(session)

        assert registry.list_identities() == ["user1"]

    def test_list_identities_multiple(self) -> None:
        """Test listing identities with multiple identities."""
        registry = IdentityRegistry()
        registry.register(IdentitySession(name="attacker"))
        registry.register(IdentitySession(name="victim"))
        registry.register(IdentitySession(name="admin"))

        identities = registry.list_identities()
        assert len(identities) == 3
        assert "attacker" in identities
        assert "victim" in identities
        assert "admin" in identities
