from enum import IntEnum
from typing import Optional


class ErrorCode(IntEnum):
    # System level errors (10000-10099)
    INTERNAL_ERROR = 10000
    INVALID_PARAMETERS = 10001
    RATELIMITER = 10002

    # Authentication related errors (10100-10199)
    AUTH_ERROR = 10100
    TOKEN_EXPIRED = 10101
    TOKEN_INVALID = 10102
    TOKEN_MISSING = 10103
    REFRESH_TOKEN_EXPIRED = 10104
    REFRESH_TOKEN_INVALID = 10105
    UNAUTHORIZED = 10106

    # User related errors (10300-10399)
    USER_NOT_FOUND = 10300
    USER_ALREADY_EXISTS = 10301
    INVALID_CREDENTIALS = 10302
    INVALID_EMAIL = 10303


class CustomAgentException(Exception):
    """Custom exception for agent-related errors."""

    def __init__(self, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR, message: Optional[str] = None):
        """
        Initialize custom exception

        Args:
            error_code: Error code
            message: Custom error message. If not provided, will use default message for the error code
        """
        self.error_code = error_code
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.error_code.name}({self.error_code}): {self.message}'
