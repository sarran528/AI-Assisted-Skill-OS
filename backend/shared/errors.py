class BusinessError(Exception):
    def __init__(self, code: str, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.context = context or {}


class SystemError(Exception):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.context = context or {}
