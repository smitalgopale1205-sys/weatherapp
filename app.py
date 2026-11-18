"""Streamlit weather app."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from weather_service import (
    CityNotFoundError,
    WeatherReport,
    WeatherService,
    WeatherServiceError,
    weather_emoji,
)

st.set_page_config(
    page_title="Weather",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(1200px 500px at 10% -10%, rgba(56, 189, 248, 0.18), transparent 55%),
          radial-gradient(900px 420px at 100% 0%, rgba(99, 102, 241, 0.16), transparent 50%),
          #0b1220;
        color: #e8eefc;
      }
      .block-container { padding-top: 2.2rem; max-width: 1100px; }
      h1, h2, h3, p, label, .stMarkdown { color: #e8eefc; }
      div[data-testid="stForm"] {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 0.4rem 1rem 0.2rem;
      }
      .hero {
        display: flex;
        justify-content: space-between;
        gap: 1.5rem;
        align-items: flex-end;
        margin: 0.4rem 0 1.2rem;
      }
      .eyebrow {
        letter-spacing: 0.16em;
        text-transform: uppercase;
        font-size: 0.75rem;
        color: #93c5fd;
        margin-bottom: 0.35rem;
      }
      .place { font-size: 2rem; font-weight: 650; line-height: 1.15; margin: 0; }
      .condition { color: #cbd5e1; margin: 0.35rem 0 0; font-size: 1.05rem; }
      .temp {
        font-size: 4.4rem;
        font-weight: 650;
        line-height: 0.9;
        letter-spacing: -0.04em;
      }
      .card {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 1rem 1.05rem 0.85rem;
        min-height: 108px;
      }
      .card .label { color: #94a3b8; font-size: 0.82rem; margin-bottom: 0.35rem; }
      .card .value { font-size: 1.45rem; font-weight: 640; }
      .card .hint { color: #cbd5e1; font-size: 0.85rem; margin-top: 0.2rem; }
      .day {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 0.9rem 0.7rem;
        text-align: center;
        min-height: 168px;
      }
      .day .when { color: #93c5fd; font-size: 0.82rem; font-weight: 640; }
      .day .icon { font-size: 1.7rem; margin: 0.35rem 0; }
      .day .range { font-weight: 650; }
      .day .meta { color: #94a3b8; font-size: 0.78rem; margin-top: 0.25rem; }
      .stButton > button, .stFormSubmitButton > button {
        background: linear-gradient(90deg, #38bdf8, #6366f1);
        color: white;
        border: 0;
        border-radius: 12px;
        font-weight: 650;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def _unit_symbol(units: str) -> str:
    return "°C" if units == "celsius" else "°F"


def _wind_symbol(units: str) -> str:
    return "km/h" if units == "celsius" else "mph"


def _format_day(iso_date: str) -> str:
    """Windows strftime does not support %-d, so pad then trim."""
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    except ValueError:
        return iso_date
    return parsed.strftime("%a %d %b").replace(" 0", " ", 1)


def _render_report(report: WeatherReport) -> None:
    symbol = _unit_symbol(report.units)
    wind = _wind_symbol(report.units)
    current = report.current
    emoji = weather_emoji(current.weather_code)

    left, right = st.columns([2.2, 1])
    with left:
        st.markdown(
            f"""
            <div class="hero">
              <div>
                <div class="eyebrow">Now</div>
                <p class="place">{report.location.label}</p>
                <p class="condition">{emoji} {current.description}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div class="temp">{current.temperature:.0f}{symbol}</div>',
            unsafe_allow_html=True,
        )

    feels, humidity, wind_col, rain = st.columns(4)
    cards = [
        (feels, "Feels like", f"{current.apparent_temperature:.0f}{symbol}", "Apparent temperature"),
        (humidity, "Humidity", f"{current.humidity_percent}%", "Relative humidity"),
        (wind_col, "Wind", f"{current.wind_speed:.0f} {wind}", "Sustained wind"),
        (rain, "Precipitation", f"{current.precipitation:.1f} mm", "Current amount"),
    ]
    for column, label, value, hint in cards:
        with column:
            st.markdown(
                f"""
                <div class="card">
                  <div class="label">{label}</div>
                  <div class="value">{value}</div>
                  <div class="hint">{hint}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 7-day forecast")
    day_columns = st.columns(len(report.daily))
    for column, day in zip(day_columns, report.daily):
        with column:
            st.markdown(
                f"""
                <div class="day">
                  <div class="when">{_format_day(day.date)}</div>
                  <div class="icon">{weather_emoji(day.weather_code)}</div>
                  <div class="range">{day.temperature_max:.0f}° / {day.temperature_min:.0f}°</div>
                  <div class="meta">{day.description}</div>
                  <div class="meta">{day.precipitation:.1f} mm</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if current.observed_at:
        st.caption(f"Observation time: {current.observed_at.replace('T', ' ')}")


def main() -> None:
    st.title("Weather")
    st.caption("Current conditions and a seven-day forecast. Data from Open-Meteo.")

    with st.form("lookup"):
        city_col, unit_col, button_col = st.columns([3, 1.2, 1])
        city = city_col.text_input("City", value="London", placeholder="Search a city")
        units_label = unit_col.selectbox("Units", ["Celsius", "Fahrenheit"])
        submitted = button_col.form_submit_button("Get weather", use_container_width=True)

    if not submitted and "report" not in st.session_state:
        st.info("Search for a city to see the forecast.")
        return

    if submitted:
        units = "celsius" if units_label == "Celsius" else "fahrenheit"
        try:
            st.session_state["report"] = WeatherService().get_weather(city, units=units)
        except CityNotFoundError as exc:
            st.warning(str(exc))
            return
        except WeatherServiceError as exc:
            st.error(str(exc))
            return

    report = st.session_state.get("report")
    if isinstance(report, WeatherReport):
        _render_report(report)


if __name__ == "__main__":
    main()
