import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Campus" in response.data


def test_dashboard_not_found(client):
    response = client.get("/dashboard/non-existent-id")
    # Redirects to index when not found
    assert response.status_code == 302


def test_interview_not_found(client):
    response = client.get("/interview/non-existent-id")
    # Redirects to index when not found
    assert response.status_code == 302
