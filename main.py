"""Banco Pichincha Unity Catalog Workshop — shareable instruction app."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "workshop.json"
FRONTEND_PATH = ROOT / "frontend"
DEFAULT_CATALOG = "diners_governance"
WORKSHOP_CATALOG = os.getenv("WORKSHOP_CATALOG", DEFAULT_CATALOG)
DEFAULT_DOMAIN_GENERAL = "payments"
DEFAULT_DOMAIN_RISK = "risk_fraud"
WORKSHOP_DOMAIN_GENERAL = os.getenv(
    "WORKSHOP_DOMAIN_GENERAL", DEFAULT_DOMAIN_GENERAL
)
WORKSHOP_DOMAIN_RISK = os.getenv("WORKSHOP_DOMAIN_RISK", DEFAULT_DOMAIN_RISK)
WORKSHOP_SENSITIVITY_HIGH = os.getenv("WORKSHOP_SENSITIVITY_HIGH", "HIGH")
WORKSHOP_SENSITIVITY_VALUES = os.getenv(
    "WORKSHOP_SENSITIVITY_VALUES", "HIGH, MEDIUM o LOW"
)
WORKSHOP_PII_VALUES = os.getenv(
    "WORKSHOP_PII_VALUES", "name, email, phone u other"
)

with DATA_PATH.open("r", encoding="utf-8") as source:
    workshop_source = source.read()

workshop_source = workshop_source.replace(DEFAULT_CATALOG, WORKSHOP_CATALOG)
workshop_source = workshop_source.replace(
    DEFAULT_DOMAIN_GENERAL, WORKSHOP_DOMAIN_GENERAL
)
workshop_source = workshop_source.replace(DEFAULT_DOMAIN_RISK, WORKSHOP_DOMAIN_RISK)
workshop_source = workshop_source.replace(
    "sensitivity=HIGH", f"sensitivity={WORKSHOP_SENSITIVITY_HIGH}"
)
workshop_source = workshop_source.replace(
    "`sensitivity` = HIGH, MEDIUM o LOW",
    f"`sensitivity` = {WORKSHOP_SENSITIVITY_VALUES}",
)
workshop_source = workshop_source.replace(
    "`pii_type` = name, email, phone u other",
    f"`pii_type` = {WORKSHOP_PII_VALUES}",
)
WORKSHOP = json.loads(workshop_source)

SECTIONS_BY_ID = {section["id"]: section for section in WORKSHOP["sections"]}

app = FastAPI(
    title="Banco Pichincha — Unity Catalog: Visión de Gobierno",
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
