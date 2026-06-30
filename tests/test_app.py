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


def test_index_with_data(client, tmp_path, monkeypatch):
    data = {
        "updated_at": "2026-06-30T10:00:00",
        "sessions": [
            {
                "cinema": "Pathé Bellecour",
                "film": "Dune 2",
                "date": "2026-06-30",
                "heure": "14:00",
                "version": "VF",
                "temperature": 36.0,
            }
        ],
    }
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    (tmp_path / "sessions.json").write_text(json.dumps(data), encoding="utf-8")
    resp = client.get("/")
    assert b"Dune 2" in resp.data


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
        "running": True, "current": 0, "total": 189,
        "cinema": "", "done": False, "count": 0, "error": None
    })
    resp = client.post("/refresh")
    assert resp.status_code == 409


def test_load_sessions_returns_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "missing.json"))
    result = flask_app.load_sessions()
    assert result == {"updated_at": None, "sessions": []}


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(flask_app, "DATA_FILE", str(tmp_path / "sessions.json"))
    data = {"updated_at": "2026-06-30T10:00:00", "sessions": [{"film": "Test"}]}
    flask_app.save_sessions(data)
    loaded = flask_app.load_sessions()
    assert loaded["sessions"][0]["film"] == "Test"
