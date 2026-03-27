from collections import defaultdict
import json
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .models import (
    get_db, User, Group, Message, hash_password,
    UserCreate, UserOut, GroupCreate, GroupResponse, MessageOut,
)
from .auth import get_current_user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for dev, lock down later
    allow_methods=["*"],
    allow_headers=["*"],
)

_ws = defaultdict(list)

async def register_client(group_id, user_id, websocket):
    await websocket.accept()
    _ws[group_id].append((user_id, websocket))


def drop_client(group_id, user_id, websocket):
    _ws[group_id] = [
        (uid, ws) for uid, ws in _ws[group_id] if ws is not websocket
    ]


async def fanout(group_id, msg):
    for _, ws in _ws[group_id]:
        await ws.send_json(msg)


async def push_presence(group_id, member_info):
    online_ids = list({uid for uid, _ in _ws[group_id]})
    online = [
        {"id": uid, **member_info.get(uid, {"name": "unknown"})}
        for uid in online_ids
    ]
    await fanout(group_id, {"type": "presence", "online": online})


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
            name=token_user["name"],
            email=token_user["email"],
            password_hash=pw_hash,
            password_salt=salt,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@app.get("/api/me", response_model=UserOut)
def me(user: User = Depends(get_authenticated_user)):
    return user


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="email already exists")
    pw_hash, salt = hash_password(payload.password)
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=pw_hash,
        password_salt=salt,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/groups", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@app.post("/api/groups", response_model=GroupResponse, status_code=201)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    group = Group(name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@app.post("/api/groups/{group_id}/members/{user_id}", status_code=204)
def add_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.get(Group, group_id)
    user = db.get(User, user_id)
    if not group or not user:
        raise HTTPException(status_code=404)
    # just ignore if already in group
    if user not in group.members:
        group.members.append(user)
        db.commit()


@app.get("/api/groups/{group_id}/messages", response_model=list[MessageOut])
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


@app.websocket("/ws/{group_id}/{user_id}")
async def chat_ws(
    websocket: WebSocket,
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    group = db.get(Group, group_id)
    if not user or not group or user not in group.members:
        await websocket.close(code=4004)
        return

    await register_client(group_id, user_id, websocket)

    member_info = {
        m.id: {"name": m.name, "last_lat": m.last_lat, "last_lng": m.last_lng}
        for m in group.members
    }
    # print(f"user {user_id} joined group {group_id}")
    await push_presence(group_id, member_info)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue

            msg = Message(
                content=content,
                sender_id=user_id,
                group_id=group_id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            await fanout(group_id, {
                "type": "message",
                "id": msg.id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "sender_id": user.id,
                "sender_name": user.name,
            })
    except WebSocketDisconnect:
        drop_client(group_id, user_id, websocket)
        await push_presence(group_id, member_info)
    except Exception as e:
        # saw this once in testing, not sure what causes it
        print(f"ws error: {e}")
        drop_client(group_id, user_id, websocket)
