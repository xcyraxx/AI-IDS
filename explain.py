import pandas as pd
import joblib
import shap
import os
import matplotlib.pyplot as plt

MODEL_PATH = "model/ids_model.pkl"
FEATURES_FILE = "data/features_advanced.csv"
ALERTS_FILE = "data/alerts.csv"
OUT_DIR = "data/explain"

os.makedirs(OUT_DIR, exist_ok=True)

def explain_latest_alert(n=1):
    if not os.path.exists(ALERTS_FILE):
        print("❌ No alerts file found.")
        return

    alerts = pd.read_csv(ALERTS_FILE)
    if alerts.empty:
        print("❌ No alerts to explain.")
        return

    df = pd.read_csv(FEATURES_FILE)

    drop_cols = [c for c in ["time", "src_ip"] if c in df.columns]
    X = df.drop(columns=drop_cols)

    model = joblib.load(MODEL_PATH)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X.tail(n))

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "shap_feature_importance.png")
    shap.summary_plot(shap_values, X.tail(n), plot_type="bar", show=False)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()

    print(f"✅ SHAP feature importance saved to {out_path}")

if __name__ == "__main__":
    explain_latest_alert(n=1)
