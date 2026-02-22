from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
from datetime import datetime
import pandas as pd
import os

app = FastAPI(title="IDS API", version="1.0")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File path
ALERTS_FILE = "data/alerts.csv"

def get_alerts_from_file():
    if not os.path.exists(ALERTS_FILE):
        return []
    try:
        # Read last 500 lines to keep it fast
        df = pd.read_csv(ALERTS_FILE)
        return df.tail(500).to_dict("records")
    except Exception as e:
        print(f"Error reading alerts: {e}")
        return []

# In-memory alert store (can be used for newly incoming alerts)
alerts: List[dict] = []

# ---------- REST APIs ----------

@app.get("/status")
def status():
    return {"backend": "ok", "ws": "ready"}

@app.get("/alerts")
def get_alerts():
    file_alerts = get_alerts_from_file()
    return file_alerts[::-1]  # newest first

@app.get("/statistics")
def statistics():
    return {
        "total_alerts": len(alerts),
        "last_alert_time": alerts[-1]["time"] if alerts else None,
    }

@app.get("/model-info")
def model_info():
    return {
        "model": "Isolation Forest",
        "window": "10s",
        "features": [
            "packet_count",
            "unique_dst_ports",
            "avg_inter_arrival",
            "protocol_entropy",
        ],
        "explainable_ai": "SHAP",
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
