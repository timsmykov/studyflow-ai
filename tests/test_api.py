import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Session, engine
from app.models import Student, Session as ChatSession
from sqlmodel import SQLModel


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture for testing."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_student(db_session):
    """Create a test student."""
    student = Student(clerk_id="test_user_123")
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


class TestHealthCheck:
    """Health check endpoint tests."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRoot:
    """Root endpoint tests."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "StudyFlow AI API"
        assert "docs" in data


class TestStudents:
    """Student endpoint tests."""

    def test_create_student(self, client, db_session):
        """Test student creation."""
        # Note: This test would need auth mocking in a real scenario
        response = client.post(
            "/students",
            json={"clerk_id": "test_user_456"}
        )
        # Expected 401 without auth
        assert response.status_code in [401, 403]

    def test_get_student_not_found(self, client):
        """Test getting non-existent student."""
        # This test would need auth mocking
        response = client.get("/students/999")
        # Expected 401 without auth
        assert response.status_code in [401, 403]


class TestBKTService:
    """BKT service tests."""

    def test_bkt_update_correct(self):
        """Test BKT mastery update with correct answer."""
        from app.services.bkt_service import BKTService

        bkt = BKTService(l0=0.2, t=0.15, g=0.1, s=0.15)

        # Correct answer should increase mastery
        new_mastery = bkt.update_mastery(current_mastery=0.5, correct=True)
        assert new_mastery > 0.5

    def test_bkt_update_incorrect(self):
        """Test BKT mastery update with incorrect answer."""
        from app.services.bkt_service import BKTService

        bkt = BKTService(l0=0.2, t=0.15, g=0.1, s=0.15)

        # Incorrect answer should decrease mastery
        new_mastery = bkt.update_mastery(current_mastery=0.8, correct=False)
        assert new_mastery < 0.8

    def test_bkt_bounds(self):
        """Test BKT mastery stays within [0, 1]."""
        from app.services.bkt_service import BKTService

        bkt = BKTService()

        # Test lower bound
        mastery = bkt.update_mastery(0.0, correct=False)
        assert 0.0 <= mastery <= 1.0

        # Test upper bound
        mastery = bkt.update_mastery(1.0, correct=True)
        assert 0.0 <= mastery <= 1.0


class TestDropoutService:
    """Dropout service tests."""

    def test_extract_features_no_student(self):
        """Test feature extraction with non-existent student."""
        from app.services.dropout_service import DropoutPredictionService

        service = DropoutPredictionService()

        with Session(engine) as db:
            features = service.extract_features(db, student_id=999999)
            assert features == {}

    def test_predict_risk_no_features(self):
        """Test dropout prediction with no features."""
        from app.services.dropout_service import DropoutPredictionService

        service = DropoutPredictionService()
        risk = service.predict_dropout_risk({})
        assert 0.0 <= risk <= 1.0

    def test_predict_risk_high_risk(self):
        """Test dropout prediction with high-risk features."""
        from app.services.dropout_service import DropoutPredictionService

        service = DropoutPredictionService()
        features = {
            "session_frequency": 0.0,
            "avg_messages_per_session": 0.0,
            "days_since_last_active": 30.0,
            "avg_session_length": 0.0,
            "avg_latency_ms": 20000.0,
            "avg_mastery": 0.0,
            "correct_rate": 0.0,
            "active_days": 0.0,
        }
        risk = service.predict_dropout_risk(features)
        assert risk > 0.5  # Should be high risk

    def test_predict_risk_low_risk(self):
        """Test dropout prediction with low-risk features."""
        from app.services.dropout_service import DropoutPredictionService

        service = DropoutPredictionService()
        features = {
            "session_frequency": 2.0,
            "avg_messages_per_session": 15.0,
            "days_since_last_active": 1.0,
            "avg_session_length": 10.0,
            "avg_latency_ms": 1000.0,
            "avg_mastery": 0.8,
            "correct_rate": 0.85,
            "active_days": 25.0,
        }
        risk = service.predict_dropout_risk(features)
        assert risk < 0.5  # Should be low risk
