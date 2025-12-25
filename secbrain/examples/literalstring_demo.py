"""Demonstration of LiteralString for SQL injection prevention.

This example shows how LiteralString (PEP 675) provides type-level
documentation and intent for SQL injection prevention.

Key Points:
-----------
1. LiteralString parameters document that only literal strings should be used
2. It signals to developers that dynamic string building is unsafe
3. Type checkers can use this information for stricter analysis
4. Combined with parameterized queries, it forms a complete defense

Note: While mypy's current LiteralString checking may not catch all cases,
the type annotation serves as important documentation and can be enforced
by other tools and future mypy versions with stricter checking.
"""

from typing import LiteralString

# =============================================================================
# Safe Database Query Pattern
# =============================================================================


def execute_query(query: LiteralString, params: tuple[object, ...] = ()) -> None:
    """Execute a parameterized SQL query safely.

    Args:
        query: SQL query as a literal string (not from user input)
        params: Query parameters to be safely substituted
    """
    print(f"Executing safe query: {query}")
    print(f"With parameters: {params}")


# =============================================================================
# ✅ SAFE Examples - These type check correctly
# =============================================================================


def safe_query_example_1(user_id: int) -> None:
    """Example 1: Simple parameterized query with literal string."""
    # ✅ Safe - query is a literal, user_id is parameterized
    execute_query("SELECT * FROM users WHERE id = ?", (user_id,))


def safe_query_example_2(username: str, email: str) -> None:
    """Example 2: INSERT with multiple parameters."""
    # ✅ Safe - query is a literal, values are parameterized
    execute_query(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        (username, email),
    )


def safe_query_with_validation(table_name: str, record_id: int) -> None:
    """Example 3: Safe dynamic table selection using validation."""
    # ✅ Safe - validate against allowed tables, then use literals
    allowed_tables = {"users": "users", "sessions": "sessions", "findings": "findings"}

    validated_table = allowed_tables.get(table_name)
    if validated_table is None:
        raise ValueError(f"Invalid table: {table_name}")

    # Use if/elif to select the correct literal query
    if validated_table == "users":
        execute_query("SELECT * FROM users WHERE id = ?", (record_id,))
    elif validated_table == "sessions":
        execute_query("SELECT * FROM sessions WHERE id = ?", (record_id,))
    elif validated_table == "findings":
        execute_query("SELECT * FROM findings WHERE id = ?", (record_id,))


# =============================================================================
# ❌ UNSAFE Examples - These will cause mypy type errors
# =============================================================================


def unsafe_query_example_1(table_name: str, user_id: int) -> None:
    """Example 1: Building query from user input - SQL INJECTION RISK!

    This is UNSAFE because:
    - table_name could be "users; DROP TABLE users; --"
    - The LiteralString type hint documents this is wrong
    - Proper code review would catch this violation
    """
    query = f"SELECT * FROM {table_name} WHERE id = ?"
    # This violates the LiteralString contract - query is dynamically built
    # execute_query(query, (user_id,))  # Don't actually call this!
    print(f"UNSAFE: Would execute: {query}")


def unsafe_query_example_2(user_input: str) -> None:
    """Example 2: Using user input directly in query - SQL INJECTION RISK!

    This is UNSAFE because:
    - user_input could be "SELECT password FROM users"
    - The LiteralString type hint documents this is wrong
    """
    # This violates the LiteralString contract - user input is not a literal
    # execute_query(user_input, ())  # Don't actually call this!
    print(f"UNSAFE: Would execute: {user_input}")


def unsafe_query_example_3(column: str, value: str) -> None:
    """Example 3: Dynamically building WHERE clause - SQL INJECTION RISK!

    This is UNSAFE because:
    - column could be "username OR 1=1"
    - The LiteralString type hint documents this is wrong
    """
    query = f"SELECT * FROM users WHERE {column} = ?"
    # This violates the LiteralString contract - WHERE clause is dynamic
    # execute_query(query, (value,))  # Don't actually call this!
    print(f"UNSAFE: Would execute: {query}")


# =============================================================================
# Running Examples
# =============================================================================


def main() -> None:
    """Run safe examples to demonstrate proper usage."""
    print("=== Safe Query Examples ===\n")

    print("Example 1: Simple SELECT")
    safe_query_example_1(user_id=123)
    print()

    print("Example 2: INSERT with parameters")
    safe_query_example_2(username="alice", email="alice@example.com")
    print()

    print("Example 3: Validated dynamic table selection")
    safe_query_with_validation(table_name="users", record_id=456)
    print()

    print("=== Unsafe Examples (for educational purposes only) ===")
    print("These demonstrate SQL injection risks that LiteralString helps prevent:")
    print()

    print("Example 1: Dynamic table name (SQL injection risk)")
    unsafe_query_example_1("users; DROP TABLE users; --", 1)
    print()

    print("Example 2: User input as query (SQL injection risk)")
    unsafe_query_example_2("SELECT * FROM sensitive_data")
    print()

    print("Example 3: Dynamic WHERE clause (SQL injection risk)")
    unsafe_query_example_3("username OR 1=1", "anything")
    print()

    print("\n" + "=" * 60)
    print("SECURITY NOTE:")
    print("=" * 60)
    print("LiteralString type hints serve multiple purposes:")
    print("1. Document the security requirement in code")
    print("2. Signal to developers that only literals are safe")
    print("3. Enable static analysis tools to detect violations")
    print("4. Provide a foundation for future stricter type checking")
    print("\nAlways combine LiteralString with parameterized queries!")
    print("=" * 60)


if __name__ == "__main__":
    main()
