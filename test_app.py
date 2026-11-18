"""Offline tests: every external API call is mocked."""
import pytest
import requests

import weather_service as ws

GEO = {"results": [
    {"name": "Paris", "admin1": "Île-de-France", "country": "France", "latitude": 48.85, "longitude": 2.35, "timezone": "Europe/Paris"},
    {"name": "Paris", "admin1": "Texas", "country": "United States", "latitude": 33.66, "longitude": -95.55, "timezone": "America/Chicago"},
]}


def forecast_payload():
    times = [f"2026-11-{18 + h // 24}T{h % 24:02d}:00" for h in range(48)]
    n = len(times)
    return {
        "timezone": "Europe/Paris",
        "current": {"time": "2026-11-18T10:15", "temperature_2m": 12.0, "apparent_temperature": 7.0,
                    "relative_humidity_2m": 81, "is_day": 1, "weather_code": 61, "pressure_msl": 1012.4,
                    "wind_speed_10m": 14.0, "visibility": 8000},
        "hourly": {"time": times, "temperature_2m": [10.0] * n, "apparent_temperature": [8.0] * n,
                   "precipitation_probability": [70] * n, "precipitation": [0.4] * n, "weather_code": [61] * n},
        "daily": {"time": [f"2026-11-{18 + i}" for i in range(7)], "weather_code": [61] * 7,
                  "temperature_2m_max": [13.0] * 7, "temperature_2m_min": [6.0] * 7,
                  "sunrise": [f"2026-11-{18 + i}T07:30" for i in range(7)],
                  "sunset": [f"2026-11-{18 + i}T17:10" for i in range(7)],
                  "precipitation_sum": [2.0] * 7, "precipitation_probability_max": [80] * 7, "uv_index_max": [1.5] * 7},
    }


AIR = {"current": {"us_aqi": 42, "pm10": 18.0, "pm2_5": 9.5, "uv_index": 2.1}}


class Resp:
    def __init__(self, data, status=200):
        self.data, self.status = data, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(str(self.status))

    def json(self):
        return self.data


@pytest.fixture
def api(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        return Resp({ws.GEO_URL: GEO, ws.FORECAST_URL: forecast_payload(), ws.AIR_URL: AIR}[url])

    monkeypatch.setattr(ws.requests, "get", fake_get)
    return calls


def test_search_cities(api):
    res = ws.search_cities("Paris")
    assert len(res) == 2
    assert res[0]["label"] == "Paris, Île-de-France, France"
    assert res[1]["latitude"] == 33.66


def test_search_short_query_skips_api(api):
    assert ws.search_cities(" a ") == []
    assert api == []


def test_search_no_results(monkeypatch):
    monkeypatch.setattr(ws.requests, "get", lambda *a, **k: Resp({}))
    assert ws.search_cities("zzzzzz") == []


def test_get_weather_parses_data(api):
    w = ws.get_weather(48.85, 2.35)
    assert w["current"]["temp"] == 12.0 and w["current"]["feels"] == 7.0
    assert w["current"]["visibility_km"] == 8.0
    assert w["current"]["uv"] == 2.1
    assert len(w["hourly"]) == 24 and w["hourly"][0]["time"] == "2026-11-18T10:00"
    assert len(w["daily"]) == 7 and w["daily"][0]["sunrise"].endswith("07:30")
    assert w["air"] == {"aqi": 42, "pm25": 9.5, "pm10": 18.0, "uv": 2.1}


def test_air_quality_failure_is_not_fatal(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return Resp(forecast_payload()) if url == ws.FORECAST_URL else Resp({}, 500)

    monkeypatch.setattr(ws.requests, "get", fake_get)
    w = ws.get_weather(1, 1)
    assert w["air"] is None and w["current"]["uv"] == 1.5


@pytest.mark.parametrize("exc, text", [(requests.Timeout(), "too long"), (requests.ConnectionError(), "Could not reach")])
def test_network_errors_raise_weather_error(monkeypatch, exc, text):
    def boom(*a, **k):
        raise exc

    monkeypatch.setattr(ws.requests, "get", boom)
    with pytest.raises(ws.WeatherError, match=text):
        ws.get_weather(1, 1)
    with pytest.raises(ws.WeatherError):
        ws.search_cities("London")


def test_http_error_raises(monkeypatch):
    monkeypatch.setattr(ws.requests, "get", lambda *a, **k: Resp({}, 503))
    with pytest.raises(ws.WeatherError):
        ws.get_weather(1, 1)


def test_incomplete_payload_raises(monkeypatch):
    monkeypatch.setattr(ws.requests, "get", lambda *a, **k: Resp({"current": {}}))
    with pytest.raises(ws.WeatherError, match="incomplete"):
        ws.get_weather(1, 1)


def test_unit_conversion():
    assert ws.c_to_f(0) == 32 and ws.c_to_f(100) == 212
    assert ws.fmt_temp(20, "C") == "20°" and ws.fmt_temp(20, "F") == "68°"
    assert ws.fmt_temp(None) == "—" and ws.convert(None, "F") is None


def test_categories_and_descriptions():
    assert ws.aqi_category(30) == "Good" and ws.aqi_category(120) == "Unhealthy for sensitive groups"
    assert ws.aqi_category(350) == "Hazardous" and ws.aqi_category(None) == "Unavailable"
    assert ws.uv_category(1) == "Low" and ws.uv_category(12) == "Extreme"
    assert ws.describe(95) == "Thunderstorm" and ws.describe(12345) == "Unknown conditions"


def test_insights_use_real_data(api):
    text = " ".join(ws.insights(ws.get_weather(1, 1), "C"))
    assert "umbrella" in text and "colder" in text and "Air quality is good" in text
    assert "9°" in " ".join(ws.insights(ws.get_weather(1, 1), "F"))
