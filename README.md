# disaster chat

quick demo for disaster response group chat.

## setup

```
docker compose up --build
```

frontend: http://localhost:3000  
keycloak admin: http://localhost:8080 (admin/admin)

test users (password is `password`):
- james.wilson@email.com
- sarah.chen@email.com
- tom.martinez@email.com

## tests

```
cd backend && python -m pytest
cd frontend && npx vitest run
```

## known issues

- websockets are in-memory, connections drop on restart
- no pagination yet
- keycloak token refresh doesn't work, just re-login
- locations are hardcoded from the seed
