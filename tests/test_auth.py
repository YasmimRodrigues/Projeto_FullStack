import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import create_app
from app.database.session import get_db
from app.models.base import Base
from app.models.user import User
from app.services.user_service import UserService
from app.utils.security import get_password_hash

# Create test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create test app
app = create_app()
app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create test database tables for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    db = TestingSessionLocal()
    hashed_password = get_password_hash("TestPassword123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def test_register(test_db):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_register_existing_username(test_user):
    """Test registration with existing username"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_register_existing_email(test_user):
    """Test registration with existing email"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "different",
            "email": "test@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login(test_user):
    """Test user login"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "WrongPassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_with_email(test_user):
    """Test login with email"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_me_endpoint(test_user):
    """Test the /me endpoint with authentication"""
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "TestPassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Access /me endpoint
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_me_endpoint_no_auth():
    """Test the /me endpoint without authentication"""
    response = client.get("/api/users/me")
    assert response.status_code == 401
