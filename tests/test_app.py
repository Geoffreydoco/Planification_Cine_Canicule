import json
import os
from unittest.mock import patch

import pytest

os.environ["TESTING"] = "1"
import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_index_returns_html(client):
    """La route / renvoie du HTML sans injecter les données."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<html" in resp.data or b"<!DOCTYPE" in resp.data


def test_sessions_json_endpoint_with_data(client, tmp_path, monkeypatch):
    data = {
        "updated_at": "2026-06-30T10:00:00",
        "sessions": [{"film": "Dune 2"}],
        "daily_temps": {"2026-06-30": {"min": 28.0, "max": 38.5}},
    }
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    (tmp_path / "sessions.json").write_text(json.dumps(data), encoding="utf-8")
    resp = client.get("/sessions.json")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["sessions"][0]["film"] == "Dune 2"
    assert "daily_temps" in body


def test_sessions_json_endpoint_empty_when_no_file(client):
    resp = client.get("/sessions.json")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["sessions"] == []
    assert "daily_temps" in body


def test_refresh_starts_background_scrape(client):
    with patch("app.threading.Thread") as mock_thread:
        mock_thread.return_value.start = lambda: None
        resp = client.post("/refresh")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["status"] == "started"


def test_progress_endpoint(client):
    resp = client.get("/progress")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert "current" in body
    assert "total" in body
    assert "done" in body


def test_refresh_rejects_concurrent_scrape(client, monkeypatch):
    monkeypatch.setattr(flask_app, "_scrape_state", {
        "running": True, "current": 0, "total": 0,
        "cinema": "", "done": False, "count": 0, "error": None
    })
    resp = client.post("/refresh")
    assert resp.status_code == 409


def test_load_sessions_returns_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "missing.json"))
    result = flask_app.load_sessions()
    assert result == {"updated_at": None, "sessions": [], "daily_temps": {}}


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    data = {"updated_at": "2026-06-30T10:00:00", "sessions": [{"film": "Test"}]}
    flask_app.save_sessions(data)
    loaded = flask_app.load_sessions()
    assert loaded["sessions"][0]["film"] == "Test"
