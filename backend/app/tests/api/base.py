import pytest
from sqlmodel import SQLModel, Session, create_engine
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.core.db import get_session


engine = create_engine(str(settings.DATABASE_URL), echo=True)


@pytest.fixture()
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def db_session(setup_db):
    db = Session(engine)
    yield db

    db.rollback()
    db.close()


@pytest.fixture()
def client(db_session):
    """
    This function returns a mock client for the API. We override the database
    session for a mocked one, avoiding using the production session.
    """
    def override_db():
        yield db_session

    app.dependency_overrides[get_session] = override_db
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_session]
