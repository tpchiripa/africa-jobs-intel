"""
FastAPI backend for the Africa Jobs Intel dashboard. Thin routing
layer only — all real logic lives in data_access.py, which is tested
independently of FastAPI (see that file's docstring).

Run locally:
    uvicorn api.main:app --reload

Then open http://127.0.0.1:8000 in a browser.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from . import data_access as da

app = FastAPI(title="Africa Jobs Intel API")

# CORS open for now since this is a small personal project serving its
# own frontend from the same origin most of the time — if the frontend
# and API ever end up on different domains in deployment, this is what
# to tighten first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/meta")
def meta():
    """Overall stats: how many roles, industries, postings, last update."""
    return da.get_meta()


@app.get("/api/snapshot")
def snapshot(top: int = Query(default=5, ge=1, le=20)):
    """Homepage snapshot: top skills across all roles, most active roles."""
    return da.get_snapshot(top_n=top)


@app.get("/api/roles/{label}")
def role_skills(label: str, top: int = Query(default=15, ge=1, le=50)):
    """Top skills for a single role."""
    result = da.get_role_skills(label, top=top)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data for role '{label}'")
    return result


@app.get("/api/roles/{label}/postings")
def role_postings(label: str, limit: int = Query(default=10, ge=1, le=30)):
    """Real job postings with direct links for a role, from its latest run."""
    return {"label": label, "postings": da.get_role_postings(label, limit=limit)}


@app.get("/api/compare")
def compare(roles: str = Query(..., description="Comma-separated role labels, e.g. data_analyst,data_engineer")):
    """Cross-role comparison for 2+ roles — only skills shared by at least 2 of them."""
    labels = [r.strip() for r in roles.split(",") if r.strip()]
    if len(labels) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 roles to compare")
    return da.get_comparison(labels)


@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    """Search for a skill (partial match) across every role's latest results."""
    return {"query": q, "results": da.search_skills(q)}


# Serve the frontend as static files, mounted last so it doesn't shadow
# the /api/* routes above. This lets the whole app deploy as one single
# service instead of needing separate frontend/backend hosting.
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
