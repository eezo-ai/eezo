# Custom exceptions for clarity and specificity
class AuthorizationError(Exception):
    """Exception raised for authorization errors."""

    pass


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found."""

    pass


class RequestError(Exception):
    """Exception raised for errors during requests."""

    pass
