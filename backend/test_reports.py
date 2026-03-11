"""
Test-on-bug: tests for bugs caught in production.

Each test documents a real bug that was found and fixed.
Run: py -3 -m pytest test_reports.py -v
"""

import json
from unittest.mock import patch, MagicMock
import pytest

# Patch env vars before importing app
import os
os.environ.setdefault("ASANA_CLIENT_ID", "fake")
os.environ.setdefault("ASANA_CLIENT_SECRET", "fake")
os.environ.setdefault("ASANA_REFRESH_TOKEN", "fake")
os.environ.setdefault("ASANA_PROJECT_GID", "123")
os.environ.setdefault("ASANA_WORKSPACE_GID", "456")

from main import app, build_idea_task, build_problem_task


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


MOCK_ASANA_RESPONSE = {"data": {"gid": "999"}}


@pytest.fixture(autouse=True)
def _reset_token_cache():
    """Clear cached access token between tests so mocks work predictably."""
    from main import _access_token_cache
    _access_token_cache["token"] = None
    _access_token_cache["expires_at"] = 0


def _mock_token_and_create(mock_post):
    """Set up mock for token exchange + task creation."""
    token_resp = MagicMock()
    token_resp.json.return_value = {"access_token": "fake-token", "expires_in": 3600}
    token_resp.raise_for_status = MagicMock()

    create_resp = MagicMock()
    create_resp.json.return_value = MOCK_ASANA_RESPONSE

    mock_post.side_effect = [token_resp, create_resp]


# ──────────────────────────────────────────────
# BUG: Idea submission returns error
# User reported idea form submit fails.
# Root cause: needs investigation, but contract must hold.
# ──────────────────────────────────────────────

class TestIdeaSubmission:
    """Bug: idea submission should create an Asana task and return success."""

    @patch("main.requests.post")
    def test_idea_returns_success(self, mock_post, client):
        _mock_token_and_create(mock_post)

        resp = client.post("/api/report", data={
            "category": "idea",
            "tg_id": "12345",
            "username": "testuser",
            "os": "Android 14",
            "device": "Honor",
            "tg_version": "9.5",
            "lang": "ru",
            "idea_title": "Add dark mode",
            "idea_description": "A dark theme for night play",
            "improvement": "Better UX at night",
        })

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert data["task_gid"] == "999"

    @patch("main.requests.post")
    def test_idea_missing_fields_returns_422(self, mock_post, client):
        resp = client.post("/api/report", data={
            "category": "idea",
            "tg_id": "12345",
            "idea_title": "",
            "idea_description": "",
            "improvement": "",
        })

        assert resp.status_code == 422

    def test_idea_notes_contain_description(self):
        data = {
            "tg_id": "12345",
            "username": "testuser",
            "os": "Android 14",
            "device": "Honor",
            "tg_version": "9.5",
            "platform": "android",
            "ram": "4",
            "battery": "50%",
            "connection": "4g",
            "useragent": "test-ua",
            "viewport_height": "824",
            "viewport_width": "360",
            "lang": "ru",
            "idea_title": "Add dark mode",
            "idea_description": "A dark theme for night play",
            "improvement": "Better UX at night",
        }

        name, html_notes = build_idea_task(data)

        assert name == "[Idea] Add dark mode"
        assert "A dark theme for night play" in html_notes
        assert "Better UX at night" in html_notes


# ──────────────────────────────────────────────
# BUG: New tech fields missing from Asana notes
# Added platform/ram/battery/connection/viewport/useragent
# but they must actually appear in the HTML notes.
# ──────────────────────────────────────────────

class TestTechFieldsInNotes:
    """Bug: new tech characteristics must appear in Asana task notes."""

    TECH_DATA = {
        "tg_id": "12345",
        "username": "tester",
        "os": "Android 14",
        "device": "Pixel 8",
        "tg_version": "9.5",
        "vpn": "no",
        "lang": "en",
        "platform": "android",
        "ram": "8",
        "battery": "72%",
        "connection": "wifi",
        "useragent": "Mozilla/5.0 Test",
        "viewport_height": "824",
        "viewport_width": "360",
    }

    def test_problem_notes_contain_all_tech_fields(self):
        data = {
            **self.TECH_DATA,
            "playback_steps": "Open app",
            "actual_result": "Crash",
            "expected_result": "No crash",
        }

        _, html_notes, _ = build_problem_task(data)

        assert "Platform: android" in html_notes
        assert "RAM: 8 GB" in html_notes
        assert "Battery: 72%" in html_notes
        assert "Connection: wifi" in html_notes
        assert "Viewport: 360×824" in html_notes
        assert "User-Agent: Mozilla/5.0 Test" in html_notes

    def test_idea_notes_contain_all_tech_fields(self):
        data = {
            **self.TECH_DATA,
            "idea_title": "Test",
            "idea_description": "Desc",
            "improvement": "Better",
        }

        _, html_notes = build_idea_task(data)

        assert "Platform: android" in html_notes
        assert "RAM: 8 GB" in html_notes
        assert "Battery: 72%" in html_notes
        assert "Connection: wifi" in html_notes
        assert "Viewport: 360×824" in html_notes
        assert "User-Agent: Mozilla/5.0 Test" in html_notes

    @patch("main.requests.post")
    def test_tech_fields_sent_to_asana(self, mock_post, client):
        """Full integration: tech fields from form reach the Asana HTML notes."""
        _mock_token_and_create(mock_post)

        resp = client.post("/api/report", data={
            "category": "idea",
            "tg_id": "12345",
            "username": "tester",
            "os": "iOS 17",
            "device": "iPhone",
            "tg_version": "9.5",
            "lang": "en",
            "platform": "ios",
            "ram": "6",
            "battery": "90%",
            "connection": "4g",
            "useragent": "Safari/17",
            "viewportHeight": "844",
            "viewportWidth": "390",
            "idea_title": "Night mode",
            "idea_description": "Add night mode",
            "improvement": "Better for eyes",
        })

        assert resp.status_code == 200

        # Verify what was sent to Asana
        create_call = mock_post.call_args_list[1]
        body = create_call[1]["json"]["data"]
        notes = body["html_notes"]

        assert "Platform: ios" in notes
        assert "RAM: 6 GB" in notes
        assert "Battery: 90%" in notes
        assert "Viewport: 390×844" in notes
