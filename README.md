# Isobar: Weather App with a CI/CD Pipeline

Streamlit + Plotly weather dashboard using live Open-Meteo data (geocoding, forecast, air quality; no API key needed). Tested with Pytest, built by Jenkins, deployed to Render.

**Features:** worldwide city search, current and feels-like temperature, humidity, wind, pressure, visibility, sunrise/sunset, 24-hour and 7-day forecasts, interactive charts, rain probability and precipitation, AQI/PM2.5/PM10, UV index, multi-city comparison, favorites, °C/°F toggle, insights, refresh, loading and error states.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -v
streamlit run app.py
```

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI |
| `weather_service.py` | Open-Meteo client, conversions, insights |
| `test_app.py` | Offline pytest suite (all API calls mocked) |
| `Jenkinsfile` | Checkout, venv, install, test, deploy |
| `render.yaml` | Render web service (auto-deploy off) |

## CI/CD setup
1. **GitHub:** push this folder to a repository (branch `main`).
2. **Render:** New > Blueprint (or Web Service), connect the repo. `render.yaml` sets build/start commands and `autoDeploy: false`, so Render never deploys on its own. Then open the service > Settings > **Deploy Hook** and copy the URL.
3. **Jenkins:** needs Python 3.10+ with `venv`, `git` and `curl` on the agent.
   - Manage Jenkins > Credentials > add **Secret text**, ID `render-deploy-hook`, value = the Render deploy hook URL.
   - New Item > Pipeline > *Pipeline script from SCM* > Git > your repo URL, branch `*/main`, script path `Jenkinsfile`.
   - Trigger builds with a GitHub webhook (`<jenkins-url>/github-webhook/`, plus the GitHub plugin's "GitHub hook trigger") or Poll SCM.
4. Push to `main`: Jenkins runs the tests and calls the deploy hook only if they pass, on `main` only. One push gives one deployment.

## Notes
- No secrets are stored in the repo; the deploy hook lives only in Jenkins credentials.
- Weather is cached for 10 minutes; **Refresh weather** clears the cache.
- Favorites are saved to `favorites.json` next to the app. On Render's free tier the disk is ephemeral, so favorites reset on redeploy.
