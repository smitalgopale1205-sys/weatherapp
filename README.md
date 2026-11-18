# Weather App

A Streamlit app that looks up current conditions and a seven-day forecast for a city. Weather data comes from the [Open-Meteo](https://open-meteo.com/) geocoding and forecast APIs, so no API key is required.

The UI lives in `app.py`. Network access and response parsing live in `weather_service.py`, which the tests exercise with a fake fetcher.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Enter a city and choose Celsius or Fahrenheit. The page shows the current temperature, feels-like temperature, humidity, wind, precipitation, and the next seven days.

## Tests

```bash
python -m pytest -q
```

Tests cover a successful lookup, unit selection, blank input, unknown cities, incomplete API payloads, and HTTP or network failures. They do not call the live weather service.

## Continuous integration

`.github/workflows/ci.yml` installs `requirements.txt` on Python 3.12 and runs `pytest` on every push and pull request.
