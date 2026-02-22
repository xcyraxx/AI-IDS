import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "model")

# File Paths
TRAFFIC_FILE = os.path.join(DATA_DIR, "traffic.csv")
FEATURES_FILE = os.path.join(DATA_DIR, "features_advanced.csv")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.csv")
SCORES_FILE = os.path.join(DATA_DIR, "scores.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "ids_model.pkl")
EXPLAIN_DIR = os.path.join(DATA_DIR, "explain")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(EXPLAIN_DIR, exist_ok=True)

# Settings
ANOMALY_THRESHOLD = 0.1
WINDOW_SIZE = "10s"
POLL_INTERVAL = 5  # seconds
MAX_BUFFER_SIZE = 200
ALLOWED_PROTOCOLS = ["TCP", "UDP", "ICMP"]
ALLOWED_PORTS = [80, 443, 22]
