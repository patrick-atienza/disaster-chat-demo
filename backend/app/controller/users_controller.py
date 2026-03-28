from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, hash_password
from app.requests import UserCreate
from app.responses import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/api/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="email already exists")
    pw_hash, salt = hash_password(payload.password)
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password_hash=pw_hash,
        password_salt=salt,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user