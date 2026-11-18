# """Isobar — a weather dashboard built on Streamlit, Plotly and Open-Meteo."""
# import json
# import os
# from datetime import datetime

# import pandas as pd
# import plotly.graph_objects as go
# import streamlit as st

# import weather_service as ws

# st.set_page_config(page_title="Isobar · Weather", page_icon="🌤", layout="wide")

# INK, ACCENT, WARM, MUTED, RULE = "#16222B", "#1F5F7A", "#B4531F", "#5C6B75", "#DCE3E7"
# FAV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")
# PAGES = ["Today", "Forecast", "Compare", "Favorites"]
# DEFAULT_CITY = {"name": "London", "country": "United Kingdom", "admin1": "England", "latitude": 51.5085,
#                 "longitude": -0.1257, "timezone": "Europe/London", "label": "London, England, United Kingdom"}

# CSS = """
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');
# html, body, .stApp, [class*="css"] {font-family:'Figtree',sans-serif; color:@INK;}
# .stApp {background:#F6F8F9;}
# [data-testid="stSidebar"] {background:#EDF1F3; border-right:1px solid @RULE;}
# [data-testid="stToolbar"], footer {display:none;}
# .block-container {padding-top:2rem; max-width:1100px;}
# h1,h2,h3 {font-family:'Source Serif 4',serif; font-weight:600; letter-spacing:-.01em;}
# .brand {font-family:'Source Serif 4',serif; font-size:1.9rem; font-weight:600; margin-bottom:.8rem;}
# .place {font-family:'Source Serif 4',serif; font-size:1.25rem; color:@MUTED;}
# .temp {font-family:'Source Serif 4',serif; font-size:6.5rem; line-height:1.05; font-weight:400;}
# .cond {font-size:1.3rem; font-weight:500; margin-bottom:.4rem;}
# .sub {color:@MUTED; line-height:1.7;}
# dl.rd {display:grid; grid-template-columns:1fr 1fr; column-gap:2.5rem; margin:0;}
# dl.rd div {display:flex; justify-content:space-between; gap:1rem; padding:.65rem 0; border-bottom:1px solid @RULE;}
# dl.rd dt {color:@MUTED;}
# dl.rd dd {margin:0; font-weight:600; text-align:right; font-variant-numeric:tabular-nums;}
# .note {border-left:3px solid @ACCENT; padding:.35rem 0 .35rem .9rem; margin:.55rem 0; max-width:62ch;}
# .stButton>button {border-radius:4px; border:1px solid @ACCENT; color:@ACCENT; background:transparent;}
# .stButton>button:hover {background:@ACCENT; color:#fff; border-color:@ACCENT;}
# @media (max-width:700px) {.temp {font-size:4.5rem;} dl.rd {grid-template-columns:1fr;}}
# </style>
# """.replace("@INK", INK).replace("@RULE", RULE).replace("@MUTED", MUTED).replace("@ACCENT", ACCENT)
# st.markdown(CSS, unsafe_allow_html=True)


# # ---------- state & helpers ----------
# def ckey(c):
#     return f"{c['latitude']:.2f},{c['longitude']:.2f}"


# def load_favs():
#     try:
#         with open(FAV_FILE, encoding="utf-8") as f:
#             return [c for c in json.load(f) if "latitude" in c]
#     except (OSError, ValueError):
#         return []


# def save_favs():
#     try:
#         with open(FAV_FILE, "w", encoding="utf-8") as f:
#             json.dump(st.session_state.favs, f)
#     except OSError:
#         pass


# ss = st.session_state
# ss.setdefault("city", DEFAULT_CITY)
# ss.setdefault("favs", load_favs())
# ss.setdefault("pool", {ckey(DEFAULT_CITY): DEFAULT_CITY})
# ss.setdefault("cmp_keys", [ckey(DEFAULT_CITY)])
# ss.setdefault("page", "Today")


# def is_fav(c):
#     return any(ckey(f) == ckey(c) for f in ss.favs)


# def toggle_fav(c):
#     ss.favs = [f for f in ss.favs if ckey(f) != ckey(c)] if is_fav(c) else ss.favs + [c]
#     save_favs()


# def open_city(c):
#     ss.city, ss.page = c, "Today"


# def add_compare(c):
#     k = ckey(c)
#     ss.pool[k] = c
#     if k not in ss.cmp_keys and len(ss.cmp_keys) < 6:
#         ss.cmp_keys = ss.cmp_keys + [k]


# def add_favs_to_compare():
#     for c in ss.favs:
#         add_compare(c)


# @st.cache_data(ttl=600, show_spinner=False)
# def load(lat, lon):
#     return ws.get_weather(lat, lon)


# @st.cache_data(ttl=3600, show_spinner=False)
# def find(q):
#     return ws.search_cities(q)


# def get(city, quiet=False):
#     try:
#         with st.spinner(f"Loading weather for {city['name']}…"):
#             return load(city["latitude"], city["longitude"])
#     except ws.WeatherError as e:
#         if not quiet:
#             st.error(f"{e} Select Refresh weather to try again.")
#         return None


# def hm(iso):
#     return datetime.fromisoformat(iso).strftime("%I:%M %p").lstrip("0") if iso else "—"


# def day(iso):
#     return datetime.fromisoformat(iso).strftime("%a %d %b")


# def num(v, fmt="{:.0f}", suffix=""):
#     return "—" if v is None else fmt.format(v) + suffix


# def style(fig, ytitle=None, h=360):
#     fig.update_layout(height=h, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
#                       plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Figtree, sans-serif", color=INK),
#                       hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0),
#                       xaxis=dict(showgrid=False, linecolor=RULE),
#                       yaxis=dict(gridcolor=RULE, zeroline=False, title=ytitle))
#     return fig


# def show(fig):
#     st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# def search_box(key, on_pick, label="Show weather"):
#     q = st.text_input("Find a city", placeholder="Try Tokyo, Nairobi or Lima", key=f"q_{key}").strip()
#     if len(q) < 2:
#         return
#     try:
#         with st.spinner("Searching cities…"):
#             res = find(q)
#     except ws.WeatherError as e:
#         st.error(str(e))
#         return
#     if not res:
#         st.caption("No city matches that name. Check the spelling or try a larger nearby city.")
#         return
#     i = st.selectbox("Matches", range(len(res)), format_func=lambda n: res[n]["label"], key=f"m_{key}")
#     st.button(label, key=f"b_{key}", on_click=on_pick, args=(res[i],))


# # ---------- sidebar ----------
# with st.sidebar:
#     st.markdown('<div class="brand">Isobar</div>', unsafe_allow_html=True)
#     st.radio("View", PAGES, key="page", label_visibility="collapsed")
#     unit = st.radio("Temperature", ["C", "F"], horizontal=True, format_func=lambda u: f"°{u}")
#     st.divider()
#     search_box("side", open_city)
#     st.divider()
#     st.button("Refresh weather", on_click=st.cache_data.clear, use_container_width=True)

# T = lambda c: ws.fmt_temp(c, unit)  # noqa: E731
# page = ss.page


# # ---------- pages ----------
# def page_today():
#     c = ss.city
#     w = get(c)
#     if not w:
#         return
#     cur, air, today = w["current"], w["air"] or {}, w["daily"][0]
#     left, right = st.columns([5, 6], gap="large")
#     with left:
#         st.markdown(
#             f'<div class="place">{c["label"]}</div><div class="temp">{T(cur["temp"])}</div>'
#             f'<div class="cond">{ws.describe(cur["code"])}</div>'
#             f'<div class="sub">Feels like {T(cur["feels"])}<br>High {T(today["tmax"])}, low {T(today["tmin"])}<br>'
#             f'Updated {hm(cur["time"])} local time</div>', unsafe_allow_html=True)
#         st.write("")
#         st.button("Remove from favorites" if is_fav(c) else "Save to favorites", on_click=toggle_fav, args=(c,))
#     rows = [
#         ("Humidity", num(cur["humidity"], suffix="%")), ("Wind", num(cur["wind"], suffix=" km/h")),
#         ("Pressure", num(cur["pressure"], suffix=" hPa")), ("Visibility", num(cur["visibility_km"], "{:.1f}", " km")),
#         ("UV index", f"{num(cur['uv'], '{:.1f}')} ({ws.uv_category(cur['uv'])})"),
#         ("Air quality (US AQI)", f"{num(air.get('aqi'))} ({ws.aqi_category(air.get('aqi'))})"),
#         ("PM2.5", num(air.get("pm25"), "{:.1f}", " µg/m³")), ("PM10", num(air.get("pm10"), "{:.1f}", " µg/m³")),
#         ("Sunrise", hm(today["sunrise"])), ("Sunset", hm(today["sunset"])),
#     ]
#     with right:
#         st.markdown('<dl class="rd">' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows) + "</dl>",
#                     unsafe_allow_html=True)
#         if not w["air"]:
#             st.caption("Air quality data is not available for this location right now.")
#     st.subheader("What to know today")
#     for line in ws.insights(w, unit):
#         st.markdown(f'<div class="note">{line}</div>', unsafe_allow_html=True)


# def page_forecast():
#     c = ss.city
#     w = get(c)
#     if not w:
#         return
#     st.subheader(c["label"])
#     t24, t7, trn = st.tabs(["Next 24 hours", "7 days", "Rain"])
#     h, d = w["hourly"], w["daily"]
#     hx = [x["time"] for x in h]
#     with t24:
#         fig = go.Figure([
#             go.Scatter(x=hx, y=[ws.convert(x["temp"], unit) for x in h], name="Temperature", mode="lines+markers",
#                        line=dict(color=ACCENT, width=3), marker=dict(size=5)),
#             go.Scatter(x=hx, y=[ws.convert(x["feels"], unit) for x in h], name="Feels like",
#                        line=dict(color=WARM, width=2, dash="dot"))])
#         show(style(fig, f"°{unit}"))
#         st.dataframe(pd.DataFrame({"Time": [hm(x) for x in hx], "Temp": [T(x["temp"]) for x in h],
#                                    "Conditions": [ws.describe(x["code"]) for x in h],
#                                    "Rain chance": [num(x["prob"], suffix="%") for x in h]}),
#                      hide_index=True, use_container_width=True)
#     with t7:
#         dx = [x["date"] for x in d]
#         fig = go.Figure([
#             go.Scatter(x=dx, y=[ws.convert(x["tmax"], unit) for x in d], name="High", mode="lines+markers",
#                        line=dict(color=WARM, width=3)),
#             go.Scatter(x=dx, y=[ws.convert(x["tmin"], unit) for x in d], name="Low", mode="lines+markers",
#                        line=dict(color=ACCENT, width=3), fill="tonexty", fillcolor="rgba(31,95,122,.08)")])
#         show(style(fig, f"°{unit}"))
#         st.dataframe(pd.DataFrame({
#             "Day": [day(x["date"]) for x in d], "Conditions": [ws.describe(x["code"]) for x in d],
#             "High": [T(x["tmax"]) for x in d], "Low": [T(x["tmin"]) for x in d],
#             "Rain chance": [num(x["prob"], suffix="%") for x in d],
#             "Rain": [num(x["precip"], "{:.1f}", " mm") for x in d], "UV max": [num(x["uv"], "{:.1f}") for x in d]}),
#             hide_index=True, use_container_width=True)
#     with trn:
#         fig = go.Figure([
#             go.Bar(x=hx, y=[x["precip"] for x in h], name="Precipitation (mm)", marker_color=ACCENT, opacity=.8),
#             go.Scatter(x=hx, y=[x["prob"] for x in h], name="Rain chance (%)", yaxis="y2",
#                        line=dict(color=WARM, width=2))])
#         style(fig, "mm")
#         fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 100], showgrid=False, title="%"))
#         show(fig)
#         st.caption(f"Expected 7-day precipitation: {sum(x['precip'] or 0 for x in d):.1f} mm.")


# def page_compare():
#     st.subheader("Compare cities")
#     with st.expander("Add a city", expanded=len(ss.cmp_keys) < 2):
#         search_box("cmp", add_compare, "Add to comparison")
#         if ss.favs:
#             st.button("Add all favorites", on_click=add_favs_to_compare)
#     st.multiselect("Cities (up to 6)", list(ss.pool), key="cmp_keys", max_selections=6,
#                    format_func=lambda k: ss.pool[k]["label"])
#     rows, fig = [], go.Figure()
#     for k in ss.cmp_keys:
#         c = ss.pool[k]
#         w = get(c, quiet=True)
#         if not w:
#             st.warning(f"Weather for {c['name']} is unavailable right now.")
#             continue
#         cur, air = w["current"], w["air"] or {}
#         probs = [x["prob"] for x in w["hourly"] if x["prob"] is not None]
#         rows.append({"City": c["label"], "Now": T(cur["temp"]), "Feels like": T(cur["feels"]),
#                      "Conditions": ws.describe(cur["code"]), "High": T(w["daily"][0]["tmax"]),
#                      "Low": T(w["daily"][0]["tmin"]), "Rain chance": num(max(probs) if probs else None, suffix="%"),
#                      "Humidity": num(cur["humidity"], suffix="%"), "Wind": num(cur["wind"], suffix=" km/h"),
#                      "AQI": num(air.get("aqi")), "UV": num(cur["uv"], "{:.1f}")})
#         fig.add_trace(go.Scatter(x=[x["date"] for x in w["daily"]], y=[ws.convert(x["tmax"], unit) for x in w["daily"]],
#                                  name=c["name"], mode="lines+markers", line=dict(width=3)))
#     if not rows:
#         st.info("Add at least two cities to compare their weather side by side.")
#         return
#     st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
#     st.markdown("**Daily highs**")
#     show(style(fig, f"°{unit}"))


# def page_favorites():
#     st.subheader("Favorite cities")
#     if not ss.favs:
#         st.info("No favorites yet. Search for a city, then choose Save to favorites on the Today view.")
#         return
#     for i, c in enumerate(ss.favs):
#         w = get(c, quiet=True)
#         a, b, v, r = st.columns([4, 3, 1, 1])
#         a.markdown(f"**{c['label']}**")
#         b.write(f"{T(w['current']['temp'])}, {ws.describe(w['current']['code'])}" if w else "Unavailable right now")
#         v.button("Open", key=f"o{i}", on_click=open_city, args=(c,))
#         r.button("Remove", key=f"r{i}", on_click=toggle_fav, args=(c,))
#         st.divider()


# {"Today": page_today, "Forecast": page_forecast, "Compare": page_compare, "Favorites": page_favorites}[page]()

"""Isobar — a weather dashboard built on Streamlit, Plotly and Open-Meteo."""
import json
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import weather_service as ws

st.set_page_config(page_title="Isobar · Weather", page_icon="🌤", layout="wide")

# ---------- palette ----------
INK      = "#14213D"  # primary text (dark navy)
MUTED    = "#475569"  # secondary text (slate-600, 7.6:1 on white)
ACCENT   = "#2563EB"  # primary blue
ACCENT_D = "#1D4ED8"  # hover blue
WARM     = "#F59E0B"  # orange (secondary chart series / status)
OK       = "#16A34A"  # green (status)
DANGER   = "#DC2626"  # red (status)
RULE     = "#E2E8F0"  # borders / gridlines
CARD     = "#FFFFFF"  # card background
BG       = "#F5F7FA"  # app background

FAV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")
PAGES = ["Today", "Forecast", "Compare", "Favorites"]
DEFAULT_CITY = {"name": "London", "country": "United Kingdom", "admin1": "England", "latitude": 51.5085,
                "longitude": -0.1257, "timezone": "Europe/London", "label": "London, England, United Kingdom"}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap');

/* ---- base ---- */
html, body, .stApp, [class*="css"] {{
  font-family: 'Figtree', system-ui, sans-serif;
  color: {INK};
  -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: {BG}; }}
.block-container {{ padding-top: 2rem; max-width: 1100px; }}

/* ---- typography ---- */
h1, h2, h3, h4 {{
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: {INK};
}}
p, span, label, li, dt, dd, .stMarkdown {{ color: {INK}; }}
.stCaption, small {{ color: {MUTED} !important; }}

/* ---- sidebar ---- */
[data-testid="stSidebar"] {{
  background: {BG};
  border-right: 1px solid {RULE};
}}
[data-testid="stSidebar"] * {{ color: {INK}; }}
[data-testid="stHeader"] {{ display: none !important; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* ---- brand / cards ---- */
.brand {{
  font-family: 'Source Serif 4', serif;
  font-size: 1.9rem;
  font-weight: 700;
  color: {INK};
  margin-bottom: .8rem;
}}
.place {{
  font-family: 'Source Serif 4', serif;
  font-size: 1.15rem;
  color: {MUTED};
  margin-bottom: .25rem;
}}
.temp {{
  font-family: 'Source Serif 4', serif;
  font-size: 6rem;
  line-height: 1.05;
  font-weight: 600;
  color: {INK};
}}
.cond {{ font-size: 1.25rem; font-weight: 600; color: {INK}; margin-bottom: .4rem; }}
.sub {{ color: {MUTED}; line-height: 1.7; }}

/* ---- definition list (metrics) ---- */
dl.rd {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 2.5rem;
  margin: 0;
  background: {CARD};
  border: 1px solid {RULE};
  border-radius: 10px;
  padding: .5rem 1.25rem;
}}
dl.rd div {{
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: .65rem 0;
  border-bottom: 1px solid {RULE};
}}
dl.rd div:last-child {{ border-bottom: none; }}
dl.rd dt {{ color: {MUTED}; }}
dl.rd dd {{
  margin: 0;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: {INK};
}}

/* ---- insight note ---- */
.note {{
  border-left: 3px solid {ACCENT};
  background: {CARD};
  border-radius: 0 8px 8px 0;
  padding: .65rem .9rem;
  margin: .55rem 0;
  max-width: 62ch;
  color: {INK};
}}

/* ---- buttons ---- */
.stButton > button, .stFormSubmitButton > button {{
  border-radius: 8px;
  border: 1px solid {ACCENT};
  color: {ACCENT};
  background: {CARD};
  font-weight: 600;
  transition: all .15s ease;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
  background: {ACCENT};
  color: #FFFFFF;
  border-color: {ACCENT_D};
}}
.stButton > button:focus {{ box-shadow: 0 0 0 3px rgba(37,99,235,.25); }}

/* ---- inputs / selects ---- */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
textarea {{
  background: {CARD} !important;
  color: {INK} !important;
  border: 1px solid {RULE} !important;
  border-radius: 8px !important;
}}

/* Fix for the invisible placeholder text */
[data-testid="stTextInput"] input::placeholder {{
  color: {MUTED} !important;
  opacity: 1 !important;
}}

/* Fix the red focus ring */
[data-testid="stTextInput"] > div > div {{
  border: 1px solid {RULE} !important;
  border-radius: 8px !important;
}}
[data-testid="stTextInput"] > div > div:focus-within {{
  border-color: {ACCENT} !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.2) !important;
}}
/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"] {{ gap: .25rem; border-bottom: 1px solid {RULE}; }}
.stTabs [data-baseweb="tab"] {{
  color: {MUTED};
  font-weight: 600;
  border-radius: 8px 8px 0 0;
  padding: .5rem 1rem;
}}
.stTabs [aria-selected="true"] {{
  color: {ACCENT} !important;
  background: {CARD};
  border-bottom: 2px solid {ACCENT};
}}

/* ---- expander / dataframe ---- */
[data-testid="stExpander"] {{
  border: 1px solid {RULE};
  border-radius: 10px;
  background: {CARD};
}}
[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; border: 1px solid {RULE}; }}

/* ---- alerts ---- */
[data-testid="stAlert"] {{ border-radius: 8px; }}
.stAlert p {{ color: {INK} !important; }}

/* ---- responsive ---- */
@media (max-width: 700px) {{
  .temp {{ font-size: 4.25rem; }}
  dl.rd {{ grid-template-columns: 1fr; padding: .25rem 1rem; }}
  .block-container {{ padding-top: 1rem; }}
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------- state & helpers ----------
def ckey(c):
    return f"{c['latitude']:.2f},{c['longitude']:.2f}"


def load_favs():
    try:
        with open(FAV_FILE, encoding="utf-8") as f:
            return [c for c in json.load(f) if "latitude" in c]
    except (OSError, ValueError):
        return []


def save_favs():
    try:
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.favs, f)
    except OSError:
        pass


ss = st.session_state
ss.setdefault("city", DEFAULT_CITY)
ss.setdefault("favs", load_favs())
ss.setdefault("pool", {ckey(DEFAULT_CITY): DEFAULT_CITY})
ss.setdefault("cmp_keys", [ckey(DEFAULT_CITY)])
ss.setdefault("page", "Today")


def is_fav(c):
    return any(ckey(f) == ckey(c) for f in ss.favs)


def toggle_fav(c):
    ss.favs = [f for f in ss.favs if ckey(f) != ckey(c)] if is_fav(c) else ss.favs + [c]
    save_favs()


def open_city(c):
    ss.city, ss.page = c, "Today"


def add_compare(c):
    k = ckey(c)
    ss.pool[k] = c
    if k not in ss.cmp_keys and len(ss.cmp_keys) < 6:
        ss.cmp_keys = ss.cmp_keys + [k]


def add_favs_to_compare():
    for c in ss.favs:
        add_compare(c)


@st.cache_data(ttl=600, show_spinner=False)
def load(lat, lon):
    return ws.get_weather(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def find(q):
    return ws.search_cities(q)


def get(city, quiet=False):
    try:
        with st.spinner(f"Loading weather for {city['name']}…"):
            return load(city["latitude"], city["longitude"])
    except ws.WeatherError as e:
        if not quiet:
            st.error(f"{e} Select Refresh weather to try again.")
        return None


def hm(iso):
    return datetime.fromisoformat(iso).strftime("%I:%M %p").lstrip("0") if iso else "—"


def day(iso):
    return datetime.fromisoformat(iso).strftime("%a %d %b")


def num(v, fmt="{:.0f}", suffix=""):
    return "—" if v is None else fmt.format(v) + suffix


def status_color(text):
    """Map existing category strings to status colors. Pure presentation."""
    t = (text or "").lower()
    if any(w in t for w in ("good", "low", "excellent", "clear")):
        return OK
    if any(w in t for w in ("moderate", "medium")):
        return WARM
    if any(w in t for w in ("poor", "high", "unhealthy", "very", "extreme", "hazardous")):
        return DANGER
    return MUTED


def style(fig, ytitle=None, h=360):
    fig.update_layout(
        height=h,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Figtree, sans-serif", color=INK, size=13),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=RULE,
                        font=dict(color=INK, family="Figtree, sans-serif")),
        legend=dict(orientation="h", y=1.12, x=0,
                    font=dict(color=INK),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor=RULE, borderwidth=1),
        xaxis=dict(showgrid=False, linecolor=RULE,
                   tickfont=dict(color=MUTED), title=None),
        yaxis=dict(gridcolor=RULE, zeroline=False, title=ytitle,
                   tickfont=dict(color=MUTED),
                   title_font=dict(color=MUTED)),
    )
    return fig


def show(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def search_box(key, on_pick, label="Show weather"):
    q = st.text_input("Find a city", placeholder="Try Tokyo, Nairobi or Lima", key=f"q_{key}").strip()
    if len(q) < 2:
        return
    try:
        with st.spinner("Searching cities…"):
            res = find(q)
    except ws.WeatherError as e:
        st.error(str(e))
        return
    if not res:
        st.caption("No city matches that name. Check the spelling or try a larger nearby city.")
        return
    i = st.selectbox("Matches", range(len(res)), format_func=lambda n: res[n]["label"], key=f"m_{key}")
    st.button(label, key=f"b_{key}", on_click=on_pick, args=(res[i],))


# ---------- sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand">Isobar</div>', unsafe_allow_html=True)
    st.radio("View", PAGES, key="page", label_visibility="collapsed")
    unit = st.radio("Temperature", ["C", "F"], horizontal=True, format_func=lambda u: f"°{u}")
    st.divider()
    search_box("side", open_city)
    st.divider()
    st.button("Refresh weather", on_click=st.cache_data.clear, use_container_width=True)

T = lambda c: ws.fmt_temp(c, unit)  # noqa: E731
page = ss.page


# ---------- pages ----------
def page_today():
    c = ss.city
    w = get(c)
    if not w:
        return
    cur, air, today = w["current"], w["air"] or {}, w["daily"][0]
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown(
            f'<div class="place">{c["label"]}</div><div class="temp">{T(cur["temp"])}</div>'
            f'<div class="cond">{ws.describe(cur["code"])}</div>'
            f'<div class="sub">Feels like {T(cur["feels"])}<br>High {T(today["tmax"])}, low {T(today["tmin"])}<br>'
            f'Updated {hm(cur["time"])} local time</div>', unsafe_allow_html=True)
        st.write("")
        st.button("Remove from favorites" if is_fav(c) else "Save to favorites", on_click=toggle_fav, args=(c,))
    uv_txt = f'{num(cur["uv"], "{:.1f}")} ({ws.uv_category(cur["uv"])})'
    aqi_txt = f'{num(air.get("aqi"))} ({ws.aqi_category(air.get("aqi"))})'
    rows = [
        ("Humidity", num(cur["humidity"], suffix="%")),
        ("Wind", num(cur["wind"], suffix=" km/h")),
        ("Pressure", num(cur["pressure"], suffix=" hPa")),
        ("Visibility", num(cur["visibility_km"], "{:.1f}", " km")),
        ("UV index", f'<span style="color:{status_color(ws.uv_category(cur["uv"]))};font-weight:700">{uv_txt}</span>'),
        ("Air quality (US AQI)",
         f'<span style="color:{status_color(ws.aqi_category(air.get("aqi")))};font-weight:700">{aqi_txt}</span>'),
        ("PM2.5", num(air.get("pm25"), "{:.1f}", " µg/m³")),
        ("PM10", num(air.get("pm10"), "{:.1f}", " µg/m³")),
        ("Sunrise", hm(today["sunrise"])),
        ("Sunset", hm(today["sunset"])),
    ]
    with right:
        st.markdown('<dl class="rd">' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows) + "</dl>",
                    unsafe_allow_html=True)
        if not w["air"]:
            st.caption("Air quality data is not available for this location right now.")
    st.subheader("What to know today")
    for line in ws.insights(w, unit):
        st.markdown(f'<div class="note">{line}</div>', unsafe_allow_html=True)


def page_forecast():
    c = ss.city
    w = get(c)
    if not w:
        return
    st.subheader(c["label"])
    t24, t7, trn = st.tabs(["Next 24 hours", "7 days", "Rain"])
    h, d = w["hourly"], w["daily"]
    hx = [x["time"] for x in h]
    with t24:
        fig = go.Figure([
            go.Scatter(x=hx, y=[ws.convert(x["temp"], unit) for x in h], name="Temperature",
                       mode="lines+markers", line=dict(color=ACCENT, width=3),
                       marker=dict(size=6, color=ACCENT)),
            go.Scatter(x=hx, y=[ws.convert(x["feels"], unit) for x in h], name="Feels like",
                       line=dict(color=WARM, width=2, dash="dot"))])
        show(style(fig, f"°{unit}"))
        st.dataframe(pd.DataFrame({"Time": [hm(x) for x in hx], "Temp": [T(x["temp"]) for x in h],
                                   "Conditions": [ws.describe(x["code"]) for x in h],
                                   "Rain chance": [num(x["prob"], suffix="%") for x in h]}),
                     hide_index=True, use_container_width=True)
    with t7:
        dx = [x["date"] for x in d]
        fig = go.Figure([
            go.Scatter(x=dx, y=[ws.convert(x["tmax"], unit) for x in d], name="High",
                       mode="lines+markers", line=dict(color=WARM, width=3),
                       marker=dict(size=7, color=WARM)),
            go.Scatter(x=dx, y=[ws.convert(x["tmin"], unit) for x in d], name="Low",
                       mode="lines+markers", line=dict(color=ACCENT, width=3),
                       marker=dict(size=7, color=ACCENT),
                       fill="tonexty", fillcolor="rgba(37,99,235,.08)")])
        show(style(fig, f"°{unit}"))
        st.dataframe(pd.DataFrame({
            "Day": [day(x["date"]) for x in d], "Conditions": [ws.describe(x["code"]) for x in d],
            "High": [T(x["tmax"]) for x in d], "Low": [T(x["tmin"]) for x in d],
            "Rain chance": [num(x["prob"], suffix="%") for x in d],
            "Rain": [num(x["precip"], "{:.1f}", " mm") for x in d],
            "UV max": [num(x["uv"], "{:.1f}") for x in d]}),
            hide_index=True, use_container_width=True)
    with trn:
        fig = go.Figure([
            go.Bar(x=hx, y=[x["precip"] for x in h], name="Precipitation (mm)",
                   marker_color=ACCENT, opacity=.85),
            go.Scatter(x=hx, y=[x["prob"] for x in h], name="Rain chance (%)", yaxis="y2",
                       line=dict(color=WARM, width=2.5))])
        style(fig, "mm")
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 100],
                                      showgrid=False, title="%",
                                      tickfont=dict(color=MUTED),
                                      title_font=dict(color=MUTED)))
        show(fig)
        st.caption(f"Expected 7-day precipitation: {sum(x['precip'] or 0 for x in d):.1f} mm.")


def page_compare():
    st.subheader("Compare cities")
    with st.expander("Add a city", expanded=len(ss.cmp_keys) < 2):
        search_box("cmp", add_compare, "Add to comparison")
        if ss.favs:
            st.button("Add all favorites", on_click=add_favs_to_compare)
    st.multiselect("Cities (up to 6)", list(ss.pool), key="cmp_keys", max_selections=6,
                   format_func=lambda k: ss.pool[k]["label"])
    rows, fig = [], go.Figure()
    CMP_COLORS = ["#2563EB", "#1D4ED8", "#3B82F6", "#60A5FA", "#0EA5E9", "#0284C7"]
    for idx, k in enumerate(ss.cmp_keys):
        c = ss.pool[k]
        w = get(c, quiet=True)
        if not w:
            st.warning(f"Weather for {c['name']} is unavailable right now.")
            continue
        cur, air = w["current"], w["air"] or {}
        probs = [x["prob"] for x in w["hourly"] if x["prob"] is not None]
        rows.append({"City": c["label"], "Now": T(cur["temp"]), "Feels like": T(cur["feels"]),
                     "Conditions": ws.describe(cur["code"]), "High": T(w["daily"][0]["tmax"]),
                     "Low": T(w["daily"][0]["tmin"]),
                     "Rain chance": num(max(probs) if probs else None, suffix="%"),
                     "Humidity": num(cur["humidity"], suffix="%"),
                     "Wind": num(cur["wind"], suffix=" km/h"),
                     "AQI": num(air.get("aqi")), "UV": num(cur["uv"], "{:.1f}")})
        fig.add_trace(go.Scatter(
            x=[x["date"] for x in w["daily"]],
            y=[ws.convert(x["tmax"], unit) for x in w["daily"]],
            name=c["name"], mode="lines+markers",
            line=dict(width=3, color=CMP_COLORS[idx % len(CMP_COLORS)]),
            marker=dict(size=7)))
    if not rows:
        st.info("Add at least two cities to compare their weather side by side.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown("**Daily highs**")
    show(style(fig, f"°{unit}"))


def page_favorites():
    st.subheader("Favorite cities")
    if not ss.favs:
        st.info("No favorites yet. Search for a city, then choose Save to favorites on the Today view.")
        return
    for i, c in enumerate(ss.favs):
        w = get(c, quiet=True)
        a, b, v, r = st.columns([4, 3, 1, 1])
        a.markdown(f"**{c['label']}**")
        b.write(f"{T(w['current']['temp'])}, {ws.describe(w['current']['code'])}" if w else "Unavailable right now")
        v.button("Open", key=f"o{i}", on_click=open_city, args=(c,))
        r.button("Remove", key=f"r{i}", on_click=toggle_fav, args=(c,))
        st.divider()


{"Today": page_today, "Forecast": page_forecast, "Compare": page_compare, "Favorites": page_favorites}[page]()