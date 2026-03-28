from collections import defaultdict
from datetime import timezone, datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Group, Message

router = APIRouter(
    prefix="/ws",
    tags=["ws"],
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


@router.websocket("/{group_id}/{user_id}")
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
