"""Unit tests for the weather service. HTTP is replaced with an in-memory fetcher."""

import json
import urllib.error

import pytest

from weather_service import (
    CityNotFoundError,
    WeatherService,
    WeatherServiceError,
    describe_weather,
    weather_emoji,
)


def _geocode_payload(name="London", country="United Kingdom", admin1="England"):
    return {
        "results": [
            {
                "name": name,
                "country": country,
                "admin1": admin1,
                "latitude": 51.5085,
                "longitude": -0.1257,
                "timezone": "Europe/London",
            }
        ]
    }


def _forecast_payload():
    return {
        "current": {
            "time": "2026-11-18T12:00",
            "temperature_2m": 12.4,
            "apparent_temperature": 10.1,
            "relative_humidity_2m": 72,
            "weather_code": 2,
            "wind_speed_10m": 18.0,
            "precipitation": 0.2,
        },
        "daily": {
            "time": ["2026-11-18", "2026-11-19"],
            "weather_code": [2, 61],
            "temperature_2m_max": [13.0, 11.5],
            "temperature_2m_min": [7.0, 6.2],
            "precipitation_sum": [0.4, 3.1],
        },
    }


class FakeFetcher:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        if not self.responses:
            raise AssertionError(f"Unexpected request: {url}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_get_weather_parses_location_current_and_daily():
    fetcher = FakeFetcher([_geocode_payload(), _forecast_payload()])
    report = WeatherService(fetcher=fetcher).get_weather("  London  ")

    assert report.location.label == "London, England, United Kingdom"
    assert report.units == "celsius"
    assert report.current.temperature == 12.4
    assert report.current.description == "Partly cloudy"
    assert report.current.humidity_percent == 72
    assert len(report.daily) == 2
    assert report.daily[1].description == "Slight rain"
    assert report.daily[1].precipitation == 3.1
    assert "name=London" in fetcher.urls[0]
    assert "temperature_unit=celsius" in fetcher.urls[1]
    assert "wind_speed_unit=kmh" in fetcher.urls[1]


def test_fahrenheit_requests_imperial_wind():
    fetcher = FakeFetcher([_geocode_payload(), _forecast_payload()])
    report = WeatherService(fetcher=fetcher).get_weather("London", units="fahrenheit")

    assert report.units == "fahrenheit"
    assert "temperature_unit=fahrenheit" in fetcher.urls[1]
    assert "wind_speed_unit=mph" in fetcher.urls[1]


def test_blank_city_is_rejected_before_any_request():
    fetcher = FakeFetcher([])
    with pytest.raises(WeatherServiceError, match="Enter a city name"):
        WeatherService(fetcher=fetcher).get_weather("   ")
    assert fetcher.urls == []


def test_invalid_units_are_rejected():
    fetcher = FakeFetcher([])
    with pytest.raises(WeatherServiceError, match="Units"):
        WeatherService(fetcher=fetcher).get_weather("London", units="kelvin")
    assert fetcher.urls == []


def test_missing_city_raises_city_not_found():
    fetcher = FakeFetcher([{"results": []}])
    with pytest.raises(CityNotFoundError, match="Atlantis"):
        WeatherService(fetcher=fetcher).get_weather("Atlantis")


def test_incomplete_geocode_payload_is_an_error():
    fetcher = FakeFetcher([{"results": [{"name": "Nowhere"}]}])
    with pytest.raises(WeatherServiceError, match="geocoding"):
        WeatherService(fetcher=fetcher).get_weather("Nowhere")


def test_incomplete_forecast_payload_is_an_error():
    fetcher = FakeFetcher([_geocode_payload(), {"current": {}, "daily": {}}])
    with pytest.raises(WeatherServiceError, match="forecast"):
        WeatherService(fetcher=fetcher).get_weather("London")


def test_empty_daily_forecast_is_an_error():
    payload = _forecast_payload()
    payload["daily"] = {
        "time": [],
        "weather_code": [],
        "temperature_2m_max": [],
        "temperature_2m_min": [],
        "precipitation_sum": [],
    }
    fetcher = FakeFetcher([_geocode_payload(), payload])
    with pytest.raises(WeatherServiceError, match="did not include"):
        WeatherService(fetcher=fetcher).get_weather("London")


def test_default_fetcher_wraps_http_and_network_errors(monkeypatch):
    def raise_http(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            "https://geocoding-api.open-meteo.com",
            503,
            "unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("weather_service.urllib.request.urlopen", raise_http)
    with pytest.raises(WeatherServiceError, match="HTTP 503"):
        WeatherService().get_weather("London")

    def raise_url(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("weather_service.urllib.request.urlopen", raise_url)
    with pytest.raises(WeatherServiceError, match="Could not reach"):
        WeatherService().get_weather("London")


def test_default_fetcher_wraps_invalid_json(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr("weather_service.urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    with pytest.raises(WeatherServiceError, match="invalid JSON"):
        WeatherService().get_weather("London")


def test_default_fetcher_rejects_non_object_json(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps([1, 2]).encode()

    monkeypatch.setattr("weather_service.urllib.request.urlopen", lambda *_args, **_kwargs: FakeResponse())
    with pytest.raises(WeatherServiceError, match="unexpected payload"):
        WeatherService().get_weather("London")


@pytest.mark.parametrize(
    ("code", "description", "emoji"),
    [
        (0, "Clear sky", "☀️"),
        (3, "Overcast", "☁️"),
        (63, "Moderate rain", "🌧️"),
        (73, "Moderate snow", "🌨️"),
        (95, "Thunderstorm", "⛈️"),
        (1234, "Unknown conditions", "🌡️"),
    ],
)
def test_weather_code_descriptions(code, description, emoji):
    assert describe_weather(code) == description
    assert weather_emoji(code) == emoji
