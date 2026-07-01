from unittest.mock import patch, Mock
import weather

FAKE_RESPONSE = {
    "hourly": {
        "time": ["2026-06-30T13:00", "2026-06-30T14:00", "2026-06-30T15:00"],
        "temperature_2m": [34.1, 36.5, 37.2],
    },
    "daily": {
        "time": ["2026-06-30"],
        "temperature_2m_min": [28.0],
        "temperature_2m_max": [38.5],
    },
}


def test_fetch_weather_returns_hourly_and_daily():
    mock_resp = Mock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("weather.requests.get", return_value=mock_resp) as mock_get:
        hourly, daily = weather.fetch_weather()

    assert hourly == {
        "2026-06-30T13:00": 34.1,
        "2026-06-30T14:00": 36.5,
        "2026-06-30T15:00": 37.2,
    }
    assert daily == {"2026-06-30": {"min": 28.0, "max": 38.5}}
    assert mock_get.call_count == 1  # un seul appel HTTP


def test_fetch_weather_combines_hourly_and_daily_params():
    mock_resp = Mock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("weather.requests.get", return_value=mock_resp) as mock_get:
        weather.fetch_weather()

    params = mock_get.call_args[1]["params"]
    assert "temperature_2m" in params["hourly"]
    assert "temperature_2m_min" in params["daily"]
    assert "temperature_2m_max" in params["daily"]


def test_get_temperature_exact_match():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-06-30", "14h00") == 36.5


def test_get_temperature_rounds_down_minutes():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-06-30", "14h30") == 36.5


def test_get_temperature_returns_none_when_missing():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-07-20", "14h00") is None


def test_get_temperature_colon_format():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-06-30", "14:30") == 36.5
