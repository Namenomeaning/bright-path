from app.core.http.exceptions import AppError


class TutorNotFound(AppError):
    status_code = 404
    code = "tutor_not_found"
    default_message = "Tutor not found"
