"""Weather lookup backed by the Open-Meteo geocoding and forecast APIs."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS = 15

WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

Fetcher = Callable[[str], dict[str, Any]]


class WeatherServiceError(Exception):
    """Base error for weather lookups that the UI can show to the user."""


class CityNotFoundError(WeatherServiceError):
    """Raised when geocoding returns no matching place."""


@dataclass(frozen=True)
class Location:
    name: str
    country: str
    admin1: str
    latitude: float
    longitude: float
    timezone: str

    @property
    def label(self) -> str:
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass(frozen=True)
class CurrentWeather:
    temperature: float
    apparent_temperature: float
    humidity_percent: int
    wind_speed: float
    precipitation: float
    weather_code: int
    description: str
    observed_at: str


@dataclass(frozen=True)
class DailyForecast:
    date: str
    weather_code: int
    description: str
    temperature_max: float
    temperature_min: float
    precipitation: float


@dataclass(frozen=True)
class WeatherReport:
    location: Location
    units: str
    current: CurrentWeather
    daily: list[DailyForecast]


def describe_weather(code: int) -> str:
    return WEATHER_CODES.get(code, "Unknown conditions")


def weather_emoji(code: int) -> str:
    if code == 0:
        return "☀️"
    if code in (1, 2):
        return "🌤️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "🌧️"
    if code in (71, 73, 75, 77, 85, 86):
        return "🌨️"
    if code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


class WeatherService:
    """Fetches a current observation and a seven-day forecast for a city name."""

    def __init__(self, fetcher: Fetcher | None = None, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self._fetcher = fetcher or self._http_get_json
        self._timeout = timeout

    def get_weather(self, city: str, units: str = "celsius") -> WeatherReport:
        query = city.strip()
        if not query:
            raise WeatherServiceError("Enter a city name.")
        if units not in ("celsius", "fahrenheit"):
            raise WeatherServiceError("Units must be celsius or fahrenheit.")

        location = self._geocode(query)
        payload = self._fetcher(self._forecast_url(location, units))
        return self._parse_report(location, units, payload)

    def _geocode(self, city: str) -> Location:
        params = urllib.parse.urlencode(
            {"name": city, "count": 1, "language": "en", "format": "json"}
        )
        payload = self._fetcher(f"{GEOCODING_URL}?{params}")
        results = payload.get("results") or []
        if not results:
            raise CityNotFoundError(f"No city found for '{city}'.")
        match = results[0]
        try:
            return Location(
                name=str(match["name"]),
                country=str(match.get("country") or ""),
                admin1=str(match.get("admin1") or ""),
                latitude=float(match["latitude"]),
                longitude=float(match["longitude"]),
                timezone=str(match.get("timezone") or "auto"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherServiceError("The geocoding response was incomplete.") from exc

    def _forecast_url(self, location: Location, units: str) -> str:
        wind_unit = "kmh" if units == "celsius" else "mph"
        params = urllib.parse.urlencode(
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timezone": location.timezone or "auto",
                "temperature_unit": units,
                "wind_speed_unit": wind_unit,
                "precipitation_unit": "mm",
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "weather_code",
                        "wind_speed_10m",
                        "precipitation",
                    ]
                ),
                "daily": ",".join(
                    [
                        "weather_code",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                    ]
                ),
                "forecast_days": 7,
            }
        )
        return f"{FORECAST_URL}?{params}"

    def _parse_report(self, location: Location, units: str, payload: dict[str, Any]) -> WeatherReport:
        current = payload.get("current") or {}
        daily = payload.get("daily") or {}
        try:
            code = int(current["weather_code"])
            observation = CurrentWeather(
                temperature=float(current["temperature_2m"]),
                apparent_temperature=float(current["apparent_temperature"]),
                humidity_percent=int(current["relative_humidity_2m"]),
                wind_speed=float(current["wind_speed_10m"]),
                precipitation=float(current["precipitation"]),
                weather_code=code,
                description=describe_weather(code),
                observed_at=str(current.get("time") or ""),
            )
            dates = daily["time"]
            codes = daily["weather_code"]
            highs = daily["temperature_2m_max"]
            lows = daily["temperature_2m_min"]
            rain = daily["precipitation_sum"]
            days = [
                DailyForecast(
                    date=str(dates[index]),
                    weather_code=int(codes[index]),
                    description=describe_weather(int(codes[index])),
                    temperature_max=float(highs[index]),
                    temperature_min=float(lows[index]),
                    precipitation=float(rain[index]),
                )
                for index in range(len(dates))
            ]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise WeatherServiceError("The forecast response was incomplete.") from exc
        if not days:
            raise WeatherServiceError("The forecast response did not include any days.")
        return WeatherReport(location=location, units=units, current=observation, daily=days)

    def _http_get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "weather-app/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise WeatherServiceError(f"Weather service returned HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            raise WeatherServiceError("Could not reach the weather service.") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WeatherServiceError("Weather service returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise WeatherServiceError("Weather service returned an unexpected payload.")
        return payload
