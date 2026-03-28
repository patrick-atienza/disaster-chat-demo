import time
import os
import requests
from sqlalchemy import text

from app.database import engine, SessionLocal
from app.models import Base, User, Group, hash_password

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")

# coords are rough - picked from google maps manually
USERS = [
    {"first_name": "James", "last_name": "Wilson", "email": "james.wilson@email.com", "last_lat": 35.6595, "last_lng": 139.7004},
    {"first_name": "Sarah", "last_name": "Chen", "email": "sarah.chen@email.com", "last_lat": 35.6614, "last_lng": 139.7036},
    {"first_name": "Tommy", "last_name": "Martinez", "email": "tom.martinez@email.com", "last_lat": 35.6580, "last_lng": 139.6982},
    {"first_name": "Emily", "last_name": "Davis", "email": "emily.davis@email.com", "last_lat": 35.6627, "last_lng": 139.6990},
    {"first_name": "Mike", "last_name": "Johnson", "email": "mike.johnson@email.com", "last_lat": 35.6563, "last_lng": 139.7020},
]


def wait_for_db(retries=30, delay=2):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            print(f"Waiting for database... ({i + 1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Database not available")


def get_keycloak_admin_token():
    # grab admin token
    resp = requests.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin",
            "grant_type": "password",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_keycloak_user(token, email, first_name, last_name="", password="password"):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # skip if they already exist
    resp = requests.get(
        f"{KEYCLOAK_URL}/admin/realms/chat/users",
        params={"username": email},
        headers=headers,
    )
    if resp.ok and resp.json():
        print(f"  keycloak user {email} already exists, skipping")
        return

    user_data = {
        "username": email,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    }
    resp = requests.post(
        f"{KEYCLOAK_URL}/admin/realms/chat/users",
        json=user_data,
        headers=headers,
    )
    if resp.status_code == 201:
        print(f"  created keycloak user: {email}")
    else:
        # sometimes keycloak is slow to accept the realm import
        print(f"  failed to create keycloak user {email}: {resp.status_code} {resp.text}")


def seed():
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # skip db seed if already seeded
    if db.query(User).first():
        print("already seeded db")
    else:
        users = []
        for u in USERS:
            pw_hash, salt = hash_password("password")
            user = User(
                first_name=u["first_name"],
                last_name=u["last_name"],
                email=u["email"],
                password_hash=pw_hash,
                password_salt=salt,
                last_lat=u["last_lat"],
                last_lng=u["last_lng"],
            )
            db.add(user)
            db.flush()
            users.append(user)

        group = Group(name="Area 1")
        group.members = users
        db.add(group)
        db.commit()
        print(f"seeded {len(users)} users in db")

    # always ensure keycloak users exist (keycloak has no persistent volume)
    try:
        token = get_keycloak_admin_token()
        for u in USERS:
            create_keycloak_user(token, u["email"], u["first_name"], u["last_name"])
    except Exception as e:
        # keycloak might not be ready yet, can always add them from admin console
        print(f"warning: couldn't seed keycloak users: {e}")

    db.close()


if __name__ == "__main__":
    seed()
