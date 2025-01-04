import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
import os

# Test database
TEST_DATABASE_URL = "postgresql://user:password@localhost/test_pult"

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

def test_get_twitter_auth_url():
    response = client.get("/api/auth/twitter/url")
    assert response.status_code == 200
    assert "url" in response.json()

def test_user_me_unauthorized():
    response = client.get("/api/user/me")
    assert response.status_code == 403

def test_enterprise_data_unauthorized():
    response = client.get("/api/enterprise/data")
    assert response.status_code == 403 