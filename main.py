"""Diners Unity Catalog Workshop — shareable instruction app."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "workshop.json"
FRONTEND_PATH = ROOT / "frontend"

with DATA_PATH.open("r", encoding="utf-8") as source:
    WORKSHOP = json.load(source)

SECTIONS_BY_ID = {section["id"]: section for section in WORKSHOP["sections"]}

app = FastAPI(
    title="Diners — Unity Catalog: Visión de Gobierno",
    version="1.0.0",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/workshop")
def get_workshop() -> dict:
    return WORKSHOP


@app.get("/api/sections")
def list_sections() -> list[dict]:
    return [
        {
            "id": section["id"],
            "title": section["title"],
            "subtitle": section["subtitle"],
            "minutes": section["minutes"],
            "stepCount": len(section["steps"]),
        }
        for section in WORKSHOP["sections"]
    ]


@app.get("/api/sections/{section_id}")
def get_section(section_id: str) -> dict:
    section = SECTIONS_BY_ID.get(section_id)
    if section is None:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")
    return section


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(FRONTEND_PATH / "favicon.svg", media_type="image/svg+xml")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_PATH / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
