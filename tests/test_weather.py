from unittest.mock import patch, Mock
import weather

FAKE_RESPONSE = {
    "hourly": {
        "time": [
            "2026-06-30T13:00",
            "2026-06-30T14:00",
            "2026-06-30T15:00",
        ],
        "temperature_2m": [34.1, 36.5, 37.2]
    }
}

def test_fetch_temperatures_returns_dict():
    mock_resp = Mock()
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_resp.raise_for_status = Mock()

    with patch("weather.requests.get", return_value=mock_resp):
        result = weather.fetch_temperatures()

    assert result == {
        "2026-06-30T13:00": 34.1,
        "2026-06-30T14:00": 36.5,
        "2026-06-30T15:00": 37.2,
    }

def test_get_temperature_exact_match():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-06-30", "14h00") == 36.5

def test_get_temperature_rounds_down_minutes():
    temps = {"2026-06-30T14:00": 36.5}
    # 14h30 -> cherche 14:00
    assert weather.get_temperature(temps, "2026-06-30", "14h30") == 36.5

def test_get_temperature_returns_none_when_missing():
    temps = {"2026-06-30T14:00": 36.5}
    assert weather.get_temperature(temps, "2026-07-20", "14h00") is None

def test_get_temperature_colon_format():
    temps = {"2026-06-30T14:00": 36.5}
    # AlloCiné new format "14:30" -> rounds down to hour 14
    assert weather.get_temperature(temps, "2026-06-30", "14:30") == 36.5
