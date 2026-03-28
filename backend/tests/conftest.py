import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.models import Base
from app.auth import get_current_user
from app.main import app

# sqlite because getting mysql running in CI was a nightmare
# also had to add check_same_thread=False or it blows up with async
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def override_get_db(db):
    def _override():
        try:
            yield db
        finally:
            pass

    def _mock_auth():
        return {"email": "testuser@email.com", "first_name": "dev", "last_name": ""}

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = _mock_auth
    yield
    app.dependency_overrides.clear()
