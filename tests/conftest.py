
"""Shared pytest fixtures for MoneyLens UG."""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

# Import all models so SQLAlchemy registers their tables.
import app.models  # noqa: F401
from app.core.database import Base
from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.main import app as fastapi_app
from app.models.user import User
from app.services.category_service import initialize_user_categories

# Load environment variables from the project's .env file.
load_dotenv()

# Read the dedicated test database URL.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing. Add it to your .env file.")

# Prevent accidental use of the development database.
database_name = make_url(TEST_DATABASE_URL).database

if database_name != "moneylens_test":
    raise RuntimeError("Automated tests must use the moneylens_test database.")


@pytest.fixture(scope="session")
def test_engine():
    """Create the SQLAlchemy engine for the test database."""

    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    # Create all registered database tables.
    Base.metadata.create_all(bind=engine)

    yield engine

    # Remove test tables after the entire test session.
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Provide an isolated database session for each test."""

    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client using the test database."""

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a synthetic user for testing."""

    user = User(
        email="pytest_user@moneylens.ug",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
    )

    db_session.add(user)
    db_session.flush()

    return user


@pytest.fixture
def auth_headers(db_session, test_user):
    """Generate authentication headers for a user with initialized categories."""

    # Initialize system categories and this user's default rules.
    initialize_user_categories(
        db=db_session,
        user_id=test_user.id,
    )

    access_token = create_access_token(str(test_user.id))

    return {"Authorization": f"Bearer {access_token}"}
