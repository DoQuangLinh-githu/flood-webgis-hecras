# backend/tests/test_api/test_simulations.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.job import SimulationJob

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    # Create test user
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="test_hash",
        role="user"
    )
    db.add(user)
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)


def test_create_simulation():
    """Test creating a simulation job"""
    response = client.post(
        "/api/simulations",
        json={
            "scenario_name": "Test Simulation",
            "rainfall": 5.0,
            "rainfall_unit": "mm",
            "duration": 5.0,
            "duration_unit": "hour"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["job_id"].startswith("JOB-")
    assert data["status"] == "QUEUED"
    assert data["scenario_name"] == "Test Simulation"
    assert data["parameters"]["rainfall"] == 5.0
    assert data["parameters"]["duration"] == 5.0


def test_get_simulation_status():
    """Test getting simulation status"""
    # Create job first
    create_response = client.post(
        "/api/simulations",
        json={
            "scenario_name": "Test Status",
            "rainfall": 10.0,
            "rainfall_unit": "mm",
            "duration": 3.0,
            "duration_unit": "hour"
        }
    )
    
    job_id = create_response.json()["job_id"]
    
    # Get status
    response = client.get(f"/api/simulations/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "QUEUED"


def test_get_all_simulations():
    """Test getting all simulations"""
    # Create multiple jobs
    for i in range(3):
        client.post(
            "/api/simulations",
            json={
                "scenario_name": f"Test {i}",
                "rainfall": 5.0 + i,
                "rainfall_unit": "mm",
                "duration": 2.0 + i,
                "duration_unit": "hour"
            }
        )
    
    response = client.get("/api/simulations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_invalid_rainfall():
    """Test validation for invalid rainfall"""
    response = client.post(
        "/api/simulations",
        json={
            "scenario_name": "Invalid Rainfall",
            "rainfall": -5.0,  # Invalid
            "rainfall_unit": "mm",
            "duration": 5.0,
            "duration_unit": "hour"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_invalid_duration():
    """Test validation for invalid duration"""
    response = client.post(
        "/api/simulations",
        json={
            "scenario_name": "Invalid Duration",
            "rainfall": 5.0,
            "rainfall_unit": "mm",
            "duration": 100.0,  # Invalid (exceeds max)
            "duration_unit": "hour"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0"