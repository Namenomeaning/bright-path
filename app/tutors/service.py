from sqlalchemy.orm import Session

from app.tutors.exceptions import TutorNotFound
from app.tutors.model import Tutor


def get_tutor(db: Session, tutor_id: str) -> Tutor:
    tutor = db.get(Tutor, tutor_id)
    if tutor is None:
        raise TutorNotFound()
    return tutor
