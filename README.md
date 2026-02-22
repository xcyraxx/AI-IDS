# AI-Powered Intrusion Detection System (AI-IDS) 🚀

This project is an AI-driven Network Intrusion Detection System that uses machine learning to detect anomalies in network traffic and provides Explainable AI (XAI) using SHAP values.

## 📁 Project Structure

```text
AI-IDS/
├── core/                # Core Engine Package
│   ├── config.py        # Centralized configuration and paths
│   ├── sniffer.py       # Packet sniffer (Scapy based)
│   ├── extractor.py     # Feature extraction from raw traffic
│   ├── detector.py      # ML Detection loop (Isolation Forest)
│   └── explainer.py     # SHAP-based explanation logic
├── data/                # Generated CSV data and SHAP plots
├── model/               # ML Model weights and training scripts
├── frontend/            # Dashboard UI (Next.js/React)
├── api.py               # FastAPI backend for the dashboard
├── run.py               # Unified orchestrator (Run this!)
└── requirements.txt     # Python dependencies
```

## 🛠 Features

- **Real-time Sniffing**: Captures TCP/UDP/ICMP traffic and logs it.
- **Advanced Feature Extraction**: Aggregates traffic into time windows (10s) and calculates statistical features (entropy, packet sizes, etc.).
- **Anomaly Detection**: Uses an Isolation Forest model to flag suspicious behavior.
- **Explainable AI (SHAP)**: Automatically generates feature importance charts when a threat is detected.
- **Interactive Dashboard**: View alerts and statistics in real-time.

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Integrated System
The `run.py` script starts the sniffer, detector, and API simultaneously using multiprocessing.
```bash
sudo python run.py
```
*(Note: `sudo` is required for packet sniffing on most systems)*

### 3. Access the API
- **URL**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs`

## 📊 Components

### Packet Sniffer
Uses `scapy` to intercept packets. Configurable via `core/config.py`.

### Detection Engine
Polls the traffic data, extracts advanced features, and runs them through the trained model. If an anomaly is found, it logs an alert and triggers the **SHAP Explainer**.

### Explainer
Calculates SHAP values for the anomalous window and saves a visualization in `data/explain/`.
