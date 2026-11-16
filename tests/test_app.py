import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Practice chess strategies",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["existing@example.edu"],
        },
        "Science Club": {
            "description": "Explore science through experiments",
            "schedule": "Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 18,
            "participants": [],
        },
    }


@pytest.fixture
def client(activity_data, monkeypatch):
    monkeypatch.setattr(app_module, "activities", activity_data)
    return TestClient(app_module.app)


def test_get_activities_returns_activity_details(client, activity_data):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_data


def test_signup_adds_participant(client, activity_data):
    email = "new@example.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activity_data["Chess Club"]["participants"] == ["existing@example.edu", email]


def test_signup_unknown_activity_returns_404(client, activity_data):
    response = client.post("/activities/Unknown%20Club/signup", params={"email": "new@example.edu"})

    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == ["existing@example.edu"]


def test_signup_duplicate_participant_returns_400_without_mutation(client, activity_data):
    participants_before = activity_data["Chess Club"]["participants"].copy()

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "existing@example.edu"},
    )

    assert response.status_code == 400
    assert activity_data["Chess Club"]["participants"] == participants_before


def test_signup_requires_email(client, activity_data):
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422
    assert activity_data["Chess Club"]["participants"] == ["existing@example.edu"]


def test_cancel_signup_removes_participant(client, activity_data):
    email = "existing@example.edu"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Cancelled signup for {email} in Chess Club"}
    assert activity_data["Chess Club"]["participants"] == []


def test_cancel_signup_unknown_activity_returns_404(client, activity_data):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "existing@example.edu"},
    )

    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == ["existing@example.edu"]


def test_cancel_unregistered_participant_returns_404_without_mutation(client, activity_data):
    participants_before = activity_data["Chess Club"]["participants"].copy()

    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "absent@example.edu"},
    )

    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == participants_before


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_index_is_served(client):
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "<html" in response.text.lower()
