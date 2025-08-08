from common.exceptions import ErrorCode

# Error message mapping
ERROR_MESSAGES = {
    # System level errors (10000-10099)
    ErrorCode.INTERNAL_ERROR: "Internal server error",
    ErrorCode.INVALID_PARAMETERS: "Invalid parameters",
    ErrorCode.RATELIMITER: "Too many requests, please try again later",

    # Authentication errors (10100-10199)
    ErrorCode.AUTH_ERROR: "Authentication failed",
    ErrorCode.TOKEN_EXPIRED: "Login session expired, please login again",
    ErrorCode.TOKEN_INVALID: "Invalid authentication token",
    ErrorCode.TOKEN_MISSING: "Please login first",
    ErrorCode.REFRESH_TOKEN_EXPIRED: "Login session expired, please login again",
    ErrorCode.REFRESH_TOKEN_INVALID: "Invalid refresh token",
    ErrorCode.UNAUTHORIZED: "Unauthorized access",
}


def get_error_message(error_code: ErrorCode, default_message: str = None) -> str:
    """
    Get error message for error code

    Args:
        error_code: Error code
        default_message: Default message to use if error code is not defined

    Returns:
        str: Error message
    """
    return ERROR_MESSAGES.get(error_code, default_message or f"Unknown error: {error_code}")
