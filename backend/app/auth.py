import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
REALM = "chat"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

security = HTTPBearer()

_jwks_client = None


def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(JWKS_URL)
    return _jwks_client


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        username = payload.get("preferred_username")
        if not username:
            raise HTTPException(status_code=401, detail="Missing username in token")
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")
        return {"email": username, "first_name": first_name, "last_name": last_name}
    except jwt.exceptions.PyJWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")
