from app.core.http.exceptions import AppError


class LessonNotFound(AppError):
    status_code = 404
    code = "lesson_not_found"
    default_message = "Lesson not found"


class NotBooked(AppError):
    status_code = 409
    code = "not_booked"
    default_message = "The lesson is not booked"


class LessonNotStarted(AppError):
    status_code = 409
    code = "lesson_not_started"
    default_message = "The lesson has not started"
