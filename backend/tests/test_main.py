import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """The /health endpoint should return a 200 and status=healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "backend-url-shortener"


def test_shorten_valid_url():
    """Shortening a valid URL should return a short_code"""
    response = client.post("/shorten", params={"original_url": "https://www.google.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert len(data["short_code"]) == 6


def test_shorten_invalid_url():
    """Shortening an invalid URL should return 400"""
    response = client.post("/shorten", params={"original_url": "not-a-real-url"})
    assert response.status_code == 400


def test_get_all_links():
    """GET /api/links should return a list"""
    response = client.get("/api/links")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_stats():
    """GET /api/stats should return total_links and total_clicks"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_links" in data
    assert "total_clicks" in data


def test_redirect_unknown_code():
    """Accessing an unknown short code should return 404"""
    response = client.get("/doesnotexist999", follow_redirects=False)
    assert response.status_code == 404
