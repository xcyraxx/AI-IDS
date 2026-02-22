import time
import pandas as pd
import joblib
import sys
import os

# Add root to path so we can import features
sys.path.append(os.getcwd())
from features.extractor import extract_advanced_features

FEATURE_FILE = "data/features_advanced.csv"
MODEL_PATH = "model/ids_model.pkl"
ALERTS_FILE = "data/alerts.csv"

# Demo-friendly threshold (tune later)
ANOMALY_THRESHOLD = 0.1

def detect_loop(poll_interval=10):
    print("🚨 IDS Detection Mode started (CTRL+C to stop)")
    model = joblib.load(MODEL_PATH)

    # Ensure alerts file exists
    try:
        pd.read_csv(ALERTS_FILE)
    except:
        pd.DataFrame(columns=["time", "src_ip", "anomaly_score", "alert"]).to_csv(ALERTS_FILE, index=False)

    last_seen_rows = 0

    while True:
        try:
            # Refresh features from raw traffic
            extract_advanced_features()
            
            df = pd.read_csv(FEATURE_FILE)

            if len(df) <= last_seen_rows:
                time.sleep(poll_interval)
                continue

            new_df = df.iloc[last_seen_rows:]
            last_seen_rows = len(df)

            print(f"🔍 Checking {len(new_df)} new rows...")

            X = new_df.select_dtypes(include=["number"])

            scores = model.decision_function(X)
            preds = model.predict(X)

            new_df["anomaly_score"] = scores
            new_df["anomaly"] = preds

            print(f"🧪 Min score in batch: {new_df['anomaly_score'].min():.4f}")

            alerts = new_df[(new_df["anomaly"] == -1) | (new_df["anomaly_score"] < ANOMALY_THRESHOLD)]

            if not alerts.empty:
                print("\n⚠️ ALERT: Anomalous activity detected!")
                for _, row in alerts.iterrows():
                    print(f"   ▶ Time: {row['time']} | Src: {row['src_ip']} | Score: {row['anomaly_score']:.4f}")

                alert_log = alerts[["time", "src_ip", "anomaly_score"]].copy()
                alert_log["alert"] = "anomaly_detected"
                alert_log.to_csv(ALERTS_FILE, mode="a", header=False, index=False)

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n🛑 Detection stopped by user.")
            break
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(poll_interval)

if __name__ == "__main__":
    detect_loop()
