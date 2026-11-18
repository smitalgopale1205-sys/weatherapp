"""Open-Meteo client and weather helpers. All data comes from live API calls."""
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
TIMEOUT = 10

WMO = {
    0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Freezing drizzle", 57: "Heavy freezing drizzle", 61: "Light rain", 63: "Rain",
    65: "Heavy rain", 66: "Freezing rain", 67: "Heavy freezing rain", 71: "Light snow",
    73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Light showers", 81: "Showers",
    82: "Violent showers", 85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}


class WeatherError(Exception):
    """Raised when weather data cannot be fetched or understood."""



def _get(url, params):
    print(f"[WEATHER DEBUG] Requesting: {url}", flush=True)

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)

        print(
    f"[WEATHER DEBUG] Status code: {getattr(resp, 'status_code', 'Not provided')}",
    flush=True
)

        resp.raise_for_status()

        data = resp.json()
        print("[WEATHER DEBUG] JSON received successfully", flush=True)

        return data

    except requests.Timeout as exc:
        print(f"[WEATHER DEBUG] TIMEOUT: {exc}", flush=True)
        raise WeatherError(
            "The weather service took too long to respond."
        ) from exc

    except requests.RequestException as exc:
        print(f"[WEATHER DEBUG] REQUEST ERROR: {exc}", flush=True)
        raise WeatherError(
            "Could not reach the weather service. Check your connection."
        ) from exc

    except ValueError as exc:
        print(f"[WEATHER DEBUG] JSON ERROR: {exc}", flush=True)
        raise WeatherError(
            "The weather service returned an unreadable response."
        ) from exc


def search_cities(query, count=8):
    """Return matching cities worldwide as dicts with name, coordinates and label."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    data = _get(GEO_URL, {"name": query, "count": count, "language": "en", "format": "json"})
    cities = []
    for r in data.get("results") or []:
        parts = [r.get("name"), r.get("admin1"), r.get("country")]
        cities.append({
            "name": r.get("name", ""), "country": r.get("country", ""), "admin1": r.get("admin1", ""),
            "latitude": r["latitude"], "longitude": r["longitude"], "timezone": r.get("timezone", "auto"),
            "label": ", ".join(p for p in parts if p),
        })
    return cities


def get_air_quality(lat, lon):
    data = _get(AIR_URL, {"latitude": lat, "longitude": lon, "timezone": "auto",
                          "current": "us_aqi,pm10,pm2_5,uv_index"})
    cur = data.get("current")
    if not cur:
        raise WeatherError("Air quality data is unavailable for this location.")
    return {"aqi": cur.get("us_aqi"), "pm25": cur.get("pm2_5"), "pm10": cur.get("pm10"), "uv": cur.get("uv_index")}


def get_weather(lat, lon):
    """Fetch and normalise current conditions, 24h hourly, 7-day daily and air quality."""
    data = _get(FORECAST_URL, {
        "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 7,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,is_day,weather_code,"
                   "pressure_msl,wind_speed_10m,visibility",
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,precipitation,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,"
                 "precipitation_sum,precipitation_probability_max,uv_index_max",
    })
    cur, hr, dy = data.get("current"), data.get("hourly"), data.get("daily")
    if not (cur and hr and dy):
        raise WeatherError("The weather service returned incomplete data.")
    try:
        air = get_air_quality(lat, lon)
    except WeatherError:
        air = None  # air quality is optional; the rest of the report still works

    hours = [{"time": t, "temp": hr["temperature_2m"][i], "feels": hr["apparent_temperature"][i],
              "prob": hr["precipitation_probability"][i], "precip": hr["precipitation"][i],
              "code": hr["weather_code"][i]} for i, t in enumerate(hr["time"])]
    start = cur["time"][:13] + ":00"
    hours = [h for h in hours if h["time"] >= start][:24]
    days = [{"date": d, "code": dy["weather_code"][i], "tmax": dy["temperature_2m_max"][i],
             "tmin": dy["temperature_2m_min"][i], "sunrise": dy["sunrise"][i], "sunset": dy["sunset"][i],
             "precip": dy["precipitation_sum"][i], "prob": dy["precipitation_probability_max"][i],
             "uv": dy["uv_index_max"][i]} for i, d in enumerate(dy["time"])]
    vis = cur.get("visibility")
    uv = (air or {}).get("uv")
    return {
        "timezone": data.get("timezone"),
        "current": {"time": cur["time"], "temp": cur.get("temperature_2m"), "feels": cur.get("apparent_temperature"),
                    "humidity": cur.get("relative_humidity_2m"), "wind": cur.get("wind_speed_10m"),
                    "pressure": cur.get("pressure_msl"), "visibility_km": None if vis is None else vis / 1000,
                    "code": cur.get("weather_code"), "is_day": cur.get("is_day"),
                    "uv": uv if uv is not None else (days[0]["uv"] if days else None)},
        "hourly": hours, "daily": days, "air": air,
    }


def c_to_f(c):
    return c * 9 / 5 + 32


def convert(c, unit="C"):
    return None if c is None else (c_to_f(c) if unit == "F" else c)


def fmt_temp(c, unit="C"):
    v = convert(c, unit)
    return "—" if v is None else f"{round(v)}°"


def describe(code):
    return WMO.get(code, "Unknown conditions")


def aqi_category(aqi):
    if aqi is None:
        return "Unavailable"
    for limit, label in [(50, "Good"), (100, "Moderate"), (150, "Unhealthy for sensitive groups"),
                         (200, "Unhealthy"), (300, "Very unhealthy")]:
        if aqi <= limit:
            return label
    return "Hazardous"


def uv_category(uv):
    if uv is None:
        return "Unavailable"
    for limit, label in [(2, "Low"), (5, "Moderate"), (7, "High"), (10, "Very high")]:
        if uv <= limit:
            return label
    return "Extreme"


def insights(w, unit="C"):
    """Plain-language recommendations derived from the fetched data."""
    cur, out = w["current"], []
    t, f = cur["temp"], cur["feels"]
    if f is not None:
        for limit, msg in [(0, "Freezing. Wear a heavy coat, gloves and a hat."),
                           (10, "Cold. A warm jacket is a good idea."),
                           (18, "Cool. A light jacket or sweater will do."),
                           (27, "Comfortable for most outdoor plans."),
                           (34, "Warm. Wear light clothing and carry water.")]:
            if f < limit:
                out.append(msg)
                break
        else:
            out.append("Very hot. Avoid long afternoon exposure and drink water regularly.")
    if t is not None and f is not None and abs(t - f) >= 4:
        d = round(abs(t - f) * (1.8 if unit == "F" else 1))
        out.append(f"It feels {d}° {'colder' if f < t else 'warmer'} than the air temperature.")
    probs = [h["prob"] for h in w["hourly"] if h["prob"] is not None]
    if probs:
        p = max(probs)
        out.append("Rain is likely (up to %d%%) in the next 24 hours. Carry an umbrella." % p if p >= 60 else
                   "Showers are possible (up to %d%%). Keep a rain layer handy." % p if p >= 30 else
                   "Rain is unlikely in the next 24 hours.")
    uv = cur["uv"]
    if uv is not None and uv >= 3:
        out.append(f"UV index is {uv_category(uv).lower()} ({uv:.0f}). Use sunscreen and sunglasses outdoors.")
    aqi = (w["air"] or {}).get("aqi")
    if aqi is not None:
        out.append("Air quality is good." if aqi <= 50 else
                   "Air quality is moderate. Unusually sensitive people should limit long outdoor effort." if aqi <= 100 else
                   "Air quality is poor. Sensitive groups should stay indoors and everyone should reduce outdoor exertion.")
    if cur["wind"] is not None and cur["wind"] >= 40:
        out.append("Strong wind. Secure loose items and take care when driving.")
    if cur["humidity"] is not None and cur["humidity"] >= 80:
        out.append("Humidity is high, so it may feel muggy.")
    if cur["visibility_km"] is not None and cur["visibility_km"] < 1:
        out.append("Visibility is low. Drive carefully.")
    return out
