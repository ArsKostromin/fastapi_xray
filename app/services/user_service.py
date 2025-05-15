from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

def create_user(db: Session, user_in: UserCreate):
    user = User(username=user_in.username, email=user_in.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
