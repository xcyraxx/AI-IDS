from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import asyncio
from datetime import datetime
import pandas as pd
import os
from core.config import ALERTS_FILE, EXPLAIN_DIR, SCORES_FILE

app = FastAPI(title="IDS API", version="1.0")

# Serve explanation images
os.makedirs(EXPLAIN_DIR, exist_ok=True)
app.mount("/explain", StaticFiles(directory=EXPLAIN_DIR), name="explain")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_data_from_file(filepath, limit=100):
    if not os.path.exists(filepath):
        return []
    try:
        df = pd.read_csv(filepath)
        return df.tail(limit).to_dict("records")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

# In-memory alert store (can be used for newly incoming alerts)
alerts: List[dict] = []

# ---------- REST APIs ----------

@app.get("/status")
def status():
    return {"backend": "ok", "ws": "ready"}

@app.get("/alerts")
def get_alerts():
    file_alerts = get_data_from_file(ALERTS_FILE, limit=500)
    return file_alerts[::-1]  # newest first

@app.get("/scores")
def get_scores():
    # Last 50 scores for the timeline
    return get_data_from_file(SCORES_FILE, limit=50)

@app.get("/statistics")
def statistics():
    file_alerts = get_data_from_file(ALERTS_FILE, limit=500)
    total = len(file_alerts)
    
    last_time = None
    avg_score = 0
    
    if total > 0:
        df = pd.DataFrame(file_alerts)
        if "time" in df.columns:
            last_time = df.iloc[0]["time"]
        if "anomaly_score" in df.columns:
            avg_score = df["anomaly_score"].mean()

    return {
        "total_alerts": total,
        "last_alert_time": last_time,
        "average_anomaly_score": round(float(avg_score), 4),
        "status": "active"
    }

@app.get("/model-info")
def model_info():
    return {
        "model": "Isolation Forest",
        "window": "10s",
        "features": [
            "packet_count",
            "avg_packet_size",
            "unique_dst_ports",
            "avg_inter_arrival",
            "protocol_entropy",
        ],
        "explainable_ai": "SHAP",
        "threshold": 0.1
    }

# Debug endpoint to simulate alerts
@app.post("/debug/add-alert")
def add_alert():
    alert = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "src_ip": "10.0.0.5",
        "anomaly_score": round(0.1 + (len(alerts) % 9) * 0.1, 2),  # demo
    }
    alerts.append(alert)
    if len(alerts) > 500:
        alerts.pop(0)
    return {"ok": True, "alert": alert}

# ---------- WebSocket ----------

@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    last_count = 0
    if os.path.exists(ALERTS_FILE):
        try:
            df = pd.read_csv(ALERTS_FILE)
            last_count = len(df)
        except:
            last_count = 0

    while True:
        try:
            if os.path.exists(ALERTS_FILE):
                df = pd.read_csv(ALERTS_FILE)
                if len(df) > last_count:
                    new_alerts = df.iloc[last_count:].to_dict("records")
                    for alert in new_alerts:
                        await ws.send_json(alert)
                    last_count = len(df)
        except Exception as e:
            print(f"WS Error: {e}")
        
        await asyncio.sleep(2)
