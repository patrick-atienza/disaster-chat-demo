from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    last_lat: float | None = None
    last_lng: float | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    members: list[UserResponse] = []


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    created_at: datetime
    sender_id: int
    group_id: int
    sender: UserResponse
