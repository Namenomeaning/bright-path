class AppError(Exception):
    """Base for every error the API returns. A subclass sets the status and the code."""

    status_code: int = 400
    code: str = "bad_request"
    default_message: str = "Bad request"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
