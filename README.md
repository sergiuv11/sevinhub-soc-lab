# SevinHub SOC Lab

## Description
A real-time SOC dashboard with log ingestion, alert system, and simulated/real log sources, designed to provide a hands-on experience in security operations. This project aims to demonstrate key components of a Security Operations Center, including data collection, real-time visualization, and incident alerting.

## Features
- **Live Log Ingestion**: Ingests structured log data from various sources.
- **Alert System**: Provides real-time alerts for INFO, WARNING, ERROR, and CRITICAL events with visual indicators.
- **Real + Simulated Logs**: Supports both real system logs (login activity) and customizable simulated logs for continuous data streams.
- **Log Agent**: A Python script (`log_agent.py`) responsible for collecting and forwarding log data to the backend.
- **Dashboard UI**: A responsive web interface for visualizing ingested logs and alerts.

## Architecture
The SevinHub SOC Lab follows a modular architecture:
`[Log Source (Real/Simulated)]` → `[log_agent.py]` → `[FastAPI Backend]` → `[Frontend Dashboard]`

- **Log Source**: Can be real system logs (e.g., login attempts, system events) or a configurable set of simulated logs.
- **`log_agent.py`**: A Python script that tails log files or generates simulated entries, then forwards them to the FastAPI Backend.
- **FastAPI Backend**: A Python web API built with FastAPI that receives, stores (in-memory for this demo), and serves log data to the frontend. It also handles various ingestion endpoints (logs, phishing, URL scans, IP scans).
- **Frontend Dashboard**: A web-based user interface built with HTML, CSS, and JavaScript (rendered via Jinja2 templates) that displays live logs, alerts, and provides forms for manual ingestion.

## Installation Steps

To set up and run the SevinHub SOC Lab, follow these steps:

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/sergiuv11/sevinhub-soc-lab.git
    cd sevinhub-soc-lab
    ```

2.  **Install Dependencies**
    Navigate to the project root and install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Backend Server**
    Start the FastAPI backend. This server will listen for log data and serve it to the frontend.
    ```bash
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
    ```
    _Keep this terminal open._

4.  **Run the Frontend Server**
    In a new terminal, start the FastAPI application that serves the frontend dashboard.
    ```bash
    uvicorn frontend.main:app --host 0.0.0.0 --port 8088
    ```
    _Keep this terminal open._

5.  **Run the Log Agent**
    In another new terminal, start the log agent. This script will automatically send logs (real or simulated) to your backend.
    ```bash
    python log_agent.py
    ```
    _Keep this terminal open. It will print messages indicating whether it's sending real or simulated logs._

## Usage

Once all three components (backend, frontend, log agent) are running:

1.  Open your web browser and navigate to:
    [http://127.0.0.1:8088](http://127.0.0.1:8088)

2.  You will see the SevinHub SOC Lab Dashboard.
    - The "Live Logs" section will automatically populate with log entries.
    - Observe the real-time alert banner and log styling for different severity levels (INFO, WARNING, ERROR, CRITICAL).
    - You can use the "Ingest Log Entry" form to manually submit logs and see them appear instantly.

## Notes
- The backend uses in-memory storage for logs, meaning data will be lost if the backend server restarts. For production, a persistent database would be used.
- The `log_agent.py` attempts to read real system logs (`/var/log/btmp`, `/var/log/wtmp`, `/var/log/lastlog`). If these are not accessible or contain no new data, it will automatically switch to sending simulated logs.
- This project is designed as a learning and portfolio piece to demonstrate core SOC dashboard functionalities.

---
