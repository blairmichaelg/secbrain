"""Contract sanitizer for optimizing LLM context window usage.

This module provides utilities to strip comments, remove large constant arrays,
and truncate repetitive patterns from smart contract source code.
"""

import re


class ContractSanitizer:
    """Sanitizes contract source code for LLM consumption."""

    @staticmethod
    def sanitize(source: str, strip_comments: bool = True, remove_large_arrays: bool = True) -> str:
        """
        Sanitize source code.
        
        Args:
            source: Raw Solidity source code
            strip_comments: Whether to remove comments
            remove_large_arrays: Whether to remove large constant arrays
            
        Returns:
            Sanitized source code
        """
        if not source:
            return ""

        sanitized = source

        if strip_comments:
            # Remove multi-line comments
            sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
            # Remove single-line comments
            sanitized = re.sub(r'//.*', '', sanitized)

        if remove_large_arrays:
            # Match large constant arrays (e.g., uint256[] private constant _data = [1, 2, ...];)
            # This is a heuristic to save tokens
            sanitized = re.sub(
                r'(constant\s+\w+\[\]\s+\w+\s*=\s*\[)[^\]]{100,}(\];)',
                r'\1/* LARGE ARRAY TRUNCATED */\2',
                sanitized
            )

        # Remove excessive whitespace
        sanitized = re.sub(r'\n\s*\n', '\n\n', sanitized)
        sanitized = sanitized.strip()

        return sanitized

    @staticmethod
    def extract_interface(source: str) -> str:
        """
        Extract only the public/external interface of the contract.
        
        Args:
            source: Raw Solidity source code
            
        Returns:
            Interface definitions
        """
        # Very basic regex-based extraction
        # In a real scenario, we might use a parser
        interfaces = []
        
        # Match function declarations
        matches = re.finditer(
            r'function\s+(\w+)\s*\([^)]*\)\s*(?:public|external)[^{]*\{',
            source
        )
        
        for match in matches:
            # Find the end of the signature (before the opening brace)
            sig = match.group(0).rstrip('{').strip()
            interfaces.append(f"{sig};")
            
        return "\n".join(interfaces)
