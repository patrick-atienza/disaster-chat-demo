from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Group, User, Message
from app.requests import GroupCreate
from app.responses import GroupResponse, MessageResponse

router = APIRouter(
    prefix="/api/groups",
    tags=["groups"],
)

@router.get("/", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    group = Group(name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.post("/{group_id}/members/{user_id}", status_code=204)
def add_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    user = db.get(User, user_id)
    if not group or not user:
        raise HTTPException(status_code=404)
    # just ignore if already in group
    if user not in group.members:
        group.members.append(user)
        db.commit()


@router.get("/{group_id}/messages", response_model=list[MessageResponse])
def get_messages(
    group_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    # TODO: pagination. offset is here but doesn't do anything yet
    return (
        db.query(Message)
        .filter(Message.group_id == group_id)
        .order_by(Message.created_at)
        .limit(limit)
        .all()
    )