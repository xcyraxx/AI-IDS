import time
import pandas as pd
import joblib
import sys
import os
from core.config import FEATURES_FILE, MODEL_PATH, ALERTS_FILE, SCORES_FILE, ANOMALY_THRESHOLD, POLL_INTERVAL
from core.extractor import extract_advanced_features
from core.explainer import explain_latest_alert

def detect_loop(poll_interval=POLL_INTERVAL):
    print("🚨 IDS Detection Mode started (CTRL+C to stop)")
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        return

    model = joblib.load(MODEL_PATH)

    # Ensure files exist
    if not os.path.exists(ALERTS_FILE):
        pd.DataFrame(columns=["time", "src_ip", "anomaly_score", "alert"]).to_csv(ALERTS_FILE, index=False)
    if not os.path.exists(SCORES_FILE):
        pd.DataFrame(columns=["time", "src_ip", "anomaly_score"]).to_csv(SCORES_FILE, index=False)

    last_seen_rows = 0

    while True:
        try:
            # Refresh features from raw traffic
            extract_advanced_features()
            
            if not os.path.exists(FEATURES_FILE):
                time.sleep(poll_interval)
                continue

            df = pd.read_csv(FEATURES_FILE)

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

            # Log all scores for the timeline
            new_df[["time", "src_ip", "anomaly_score"]].to_csv(SCORES_FILE, mode="a", header=False, index=False)

            print(f"🧪 Min score in batch: {new_df['anomaly_score'].min():.4f}")

            alerts = new_df[(new_df["anomaly"] == -1) | (new_df["anomaly_score"] < ANOMALY_THRESHOLD)]

            if not alerts.empty:
                print("\n⚠️ ALERT: Anomalous activity detected!")
                for _, row in alerts.iterrows():
                    print(f"   ▶ Time: {row['time']} | Src: {row['src_ip']} | Score: {row['anomaly_score']:.4f}")

                alert_log = alerts[["time", "src_ip", "anomaly_score"]].copy()
                alert_log["alert"] = "anomaly_detected"
                alert_log.to_csv(ALERTS_FILE, mode="a", header=False, index=False)

                # TRIGGER EXPLAINER
                print("🧠 Generating explanation for the latest alert...")
                explain_latest_alert(n=1)

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n🛑 Detection stopped by user.")
            break
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(poll_interval)

if __name__ == "__main__":
    detect_loop()
