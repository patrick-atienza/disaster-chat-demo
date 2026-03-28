from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .controller import ws_controller, users_controller, groups_controller
from .models import User, hash_password
from .responses import UserResponse

app = FastAPI()

app.include_router(users_controller.router)
app.include_router(groups_controller.router)
app.include_router(ws_controller.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for dev, lock down later
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_authenticated_user(
    token_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # auto-register from keycloak on first login
    user = db.query(User).filter(
        User.email == token_user["email"]
    ).first()
    if not user:
        pw_hash, salt = hash_password("password")
        user = User(
            first_name=token_user["first_name"],
            last_name=token_user["last_name"],
            email=token_user["email"],
            password_hash=pw_hash,
            password_salt=salt,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@app.get("/api/me", response_model=UserResponse)
def me(user: User = Depends(get_authenticated_user)):
    return user

