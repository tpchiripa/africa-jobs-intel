# Deploying the dashboard

The app is a single FastAPI service that serves both the `/api/*` endpoints
and the static frontend (`static/index.html`, `style.css`, `app.js`) from
one process — no separate frontend hosting needed.

## Test locally first

```
venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Then open http://127.0.0.1:8000 in a browser. Confirm the role chips load,
a single role shows its skill bars, compare mode shows the heat grid for
2+ selected roles, and search returns results. Fix anything broken here
before deploying — much faster to debug locally than on a live server.

## Deploy on Render (free tier available)

1. Push this repo to GitHub if you haven't already (it already is).
2. Go to [render.com](https://render.com), sign up/log in, click
   **New +** → **Web Service**.
3. Connect your GitHub account and select the `africa-jobs-intel` repo.
4. Render should auto-detect the `Procfile`. If it asks for a start
   command manually, use:
   ```
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
5. Build command: `pip install -r requirements.txt`
6. Choose the **Free** instance type.
7. Click **Create Web Service**. First deploy takes a few minutes.
8. Once live, Render gives you a URL like
   `https://africa-jobs-intel.onrender.com` — that's the whole
   dashboard, live.

## Known limitation of Render's free tier

Free-tier services spin down after ~15 minutes of no traffic and take
10-30 seconds to wake up on the next request. Fine for a portfolio piece
someone visits occasionally; not fine for something you'd expect to
always be instantly responsive. Upgrading to a paid tier removes this
if it ever matters.

## Updating the live data

The dashboard reads `data/skill_demand_log.csv` at request time — it
doesn't cache a snapshot at deploy time. So the normal workflow is:

```
python scrapers\fetch_adzuna.py "some role"
python analysis\skill_extraction.py data\raw\some_role.csv
git add data\skill_demand_log.csv data\raw\some_role.csv
git commit -m "Add <role> data"
git push
```

Render auto-redeploys on every push to the connected branch, so pushing
new data is enough to update the live dashboard — no separate deploy
step needed.
