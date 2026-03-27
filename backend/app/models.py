import os
import hashlib
from sqlalchemy import (
    Column, Integer, String, Text,
    Float, ForeignKey, Table,
    DateTime, create_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://chat:chat@localhost:3306/chat",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


group_members = Table(
    "group_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32).hex()
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), bytes.fromhex(salt), 100_000
    ).hex()
    return pw_hash, salt


def verify_password(password, pw_hash, salt):
    check, _ = hash_password(password, salt)
    return check == pw_hash


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    password_salt = Column(String(64), nullable=False)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)

    messages = relationship("Message", back_populates="sender")
    groups = relationship(
        "Group",
        secondary=group_members,
        back_populates="members",
    )


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    members = relationship(
        "User",
        secondary=group_members,
        back_populates="groups",
    )
    messages = relationship(
        "Message",
        back_populates="group",
        order_by="Message.created_at",
    )

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    sender = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")


# schemas

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    last_lat: float | None = None
    last_lng: float | None = None


class GroupCreate(BaseModel):
    name: str


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    members: list[UserOut] = []


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    created_at: datetime
    sender_id: int
    group_id: int
    sender: UserOut
