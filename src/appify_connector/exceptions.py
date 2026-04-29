class AppifyConnectorError(Exception):
    status_code: int = 500
    code: str = "INTERNAL"

    def __init__(self, message: str = "") -> None:
        self.message = message or self.__class__.__name__
        super().__init__(self.message)


class AppifyAuthError(AppifyConnectorError):
    status_code = 401
    code = "APPIFY_AUTH_FAILED"


class AppifyUpstreamError(AppifyConnectorError):
    status_code = 502
    code = "APPIFY_UPSTREAM_ERROR"


class SessionExpired(AppifyConnectorError):
    status_code = 401
    code = "SESSION_EXPIRED"


class ObjectNotFound(AppifyConnectorError):
    status_code = 404
    code = "OBJECT_NOT_FOUND"
