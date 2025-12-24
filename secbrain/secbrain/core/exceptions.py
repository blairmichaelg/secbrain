"""Custom exceptions for SecBrain."""


class SecBrainError(Exception):
    """Base exception for all SecBrain errors."""


class ValidationError(SecBrainError):
    """Raised when validation fails."""


class CompilationError(SecBrainError):
    """Raised when contract compilation fails."""

    def __init__(
        self,
        message: str,
        *,
        contract: str = "",
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.contract = contract
        self.stdout = stdout
        self.stderr = stderr


class RateLimitError(SecBrainError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, *, retry_after: float = 0.0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class InsufficientProfitError(SecBrainError):
    """Raised when exploit profit is below threshold."""

    def __init__(
        self,
        message: str,
        *,
        actual_profit: float = 0.0,
        threshold: float = 0.0,
    ) -> None:
        super().__init__(message)
        self.actual_profit = actual_profit
        self.threshold = threshold
