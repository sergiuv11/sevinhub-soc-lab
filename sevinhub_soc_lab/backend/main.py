from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import os

from .database import SessionLocal, engine, Base, CaseHistory, get_db

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SevinHub SOC Lab API",
    description="Backend API for the SevinHub SOC Lab platform."
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="sevinhub_soc_lab/frontend"), name="static")

# Serve index.html at the root
@app.get("/")
async def serve_frontend():
    return FileResponse("sevinhub_soc_lab/frontend/index.html")

# Placeholder for SOC Analyst Agent
@app.post("/analyze")
async def analyze_indicator():
    # TODO: Implement actual analysis logic
    return {"message": "Analysis endpoint - Coming Soon!"}

# Placeholder for Incident Simulator
@app.get("/incidents")
async def get_incidents():
    # TODO: Load incidents from data/incidents.json
    return {"message": "Incident simulator - Coming Soon!"}

# Placeholder for Threat Map data
@app.get("/threats")
async def get_threat_data():
    # TODO: Generate simulated threat data
    return {"message": "Threat map data - Coming Soon!"}

# Placeholder for SOC Score and Threat Level
@app.get("/status")
async def get_soc_status():
    # TODO: Return actual SOC score and threat level
    return {"soc_score": 75, "threat_level": "Medium", "message": "SOC Status - Coming Soon!"}

# Placeholder for Case History
@app.get("/history", response_model=List[dict]) # Use dict for now, Pydantic model later
async def get_case_history(db: Session = Depends(get_db)):
    history = db.query(CaseHistory).all()
    return [{ "id": h.id, "indicator": h.indicator, "threat_score": h.threat_score, "classification": h.classification, "timestamp": h.timestamp.isoformat(), "notes": h.notes } for h in history]

@app.post("/history")
async def add_case_history(item: dict, db: Session = Depends(get_db)):
    # TODO: Use Pydantic model for item validation
    db_item = CaseHistory(indicator=item['indicator'], threat_score=item['threat_score'], classification=item['classification'], notes=item.get('notes'))
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Placeholder for Reports
@app.post("/report")
async def generate_report():
    # TODO: Implement report generation logic
    return {"message": "Report generation - Coming Soon!"}
