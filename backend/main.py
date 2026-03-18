from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, IPvAnyAddress
from datetime import datetime
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:8088",  # Frontend running locally
    "http://127.0.0.1:8088", # Frontend running locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogEntry(BaseModel):
    timestamp: datetime
    source: str
    level: str
    message: str

# In-memory storage for logs for demonstration purposes
logs_db: List[LogEntry] = []

class PhishingReport(BaseModel):
    timestamp: datetime
    reporter_email: str
    reported_url: HttpUrl
    screenshot_url: Optional[HttpUrl] = None
    subject: Optional[str] = None
    body_snippet: Optional[str] = None

class URLScan(BaseModel):
    timestamp: datetime
    url: HttpUrl
    scanner: str
    result: dict

class IPScan(BaseModel):
    timestamp: datetime
    ip_address: IPvAnyAddress
    scanner: str
    result: dict

@app.get("/")
async def read_root():
    return {"message": "Welcome to SevinHub SOC Lab Backend!"}

@app.post("/ingest/log")
async def ingest_log(log_entry: LogEntry):
    logs_db.append(log_entry) # Store the log
    print(f"Received log: {log_entry.dict()}")
    return {"status": "success", "message": "Log ingested successfully", "log_data": log_entry.dict()}

@app.get("/logs", response_model=List[LogEntry])
async def get_logs():
    return logs_db

@app.post("/ingest/phishing")
async def ingest_phishing_report(report: PhishingReport):
    print(f"Received phishing report: {report.dict()}")
    return {"status": "success", "message": "Phishing report ingested successfully", "report_data": report.dict()}

@app.post("/ingest/url_scan")
async def ingest_url_scan(scan: URLScan):
    print(f"Received URL scan result: {scan.dict()}")
    return {"status": "success", "message": "URL scan ingested successfully", "scan_data": scan.dict()}

@app.post("/ingest/ip_scan")
async def ingest_ip_scan(scan: IPScan):
    print(f"Received IP scan result: {scan.dict()}")
    return {"status": "success", "message": "IP scan ingested successfully", "scan_data": scan.dict()}
