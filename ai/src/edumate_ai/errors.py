class AIError(Exception):
    """Portable AI failure; consumers decide how to expose it over their API."""

    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)
