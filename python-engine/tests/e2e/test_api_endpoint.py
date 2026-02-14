"""
test_api_endpoint.py — API Contract Verification
====================================================
Tests the FastAPI endpoints using TestClient.
Validates HTTP status, response schema, and data types.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_model):
    """Create a TestClient with the mocked NLP model."""
    from app.main import app
    return TestClient(app)


class TestOracleEndpoint:
    def test_returns_200(self, client):
        response = client.get("/oracle")
        assert response.status_code == 200

    def test_returns_valid_json(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert isinstance(data, dict)

    def test_response_schema(self, client):
        """All required fields must be present."""
        response = client.get("/oracle")
        data = response.json()
        assert "raw_score" in data
        assert "smoothed_score" in data
        assert "post_count" in data
        assert "positive_count" in data
        assert "negative_count" in data
        assert "last_updated_timestamp" in data

    def test_score_types(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert isinstance(data["raw_score"], (int, float))
        assert isinstance(data["smoothed_score"], (int, float))
        assert isinstance(data["post_count"], int)
        assert isinstance(data["positive_count"], int)
        assert isinstance(data["negative_count"], int)
        assert isinstance(data["last_updated_timestamp"], str)

    def test_score_bounds(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert -100 <= data["raw_score"] <= 100
        assert -100 <= data["smoothed_score"] <= 100

    def test_counts_non_negative(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert data["post_count"] >= 0
        assert data["positive_count"] >= 0
        assert data["negative_count"] >= 0

    def test_counts_consistent(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert data["positive_count"] + data["negative_count"] == data["post_count"]

    def test_timestamp_present_and_nonempty(self, client):
        response = client.get("/oracle")
        data = response.json()
        assert len(data["last_updated_timestamp"]) > 0

    def test_timestamp_iso_format(self, client):
        """Timestamp should be valid ISO 8601."""
        from datetime import datetime
        response = client.get("/oracle")
        data = response.json()
        # Should not raise
        dt = datetime.fromisoformat(data["last_updated_timestamp"])
        assert dt is not None


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "sentiment-oracle"


class TestInvalidEndpoints:
    def test_unknown_route_returns_404(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_post_to_oracle_not_allowed(self, client):
        response = client.post("/oracle")
        assert response.status_code == 405


class TestMultipleRequests:
    def test_consecutive_requests_succeed(self, client):
        """Multiple sequential requests should all succeed."""
        for _ in range(5):
            response = client.get("/oracle")
            assert response.status_code == 200
            data = response.json()
            assert -100 <= data["raw_score"] <= 100
