class PrismError(Exception):
    """Base class for errors the API turns into friendly JSON responses."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ConfigError(PrismError):
    code = "config_error"


class UnauthorizedError(PrismError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(PrismError):
    status_code = 403
    code = "forbidden"


class ValidationError(PrismError):
    status_code = 400
    code = "invalid_request"
