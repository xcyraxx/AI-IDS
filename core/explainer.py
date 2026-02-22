import pandas as pd
import joblib
import shap
import os
import matplotlib.pyplot as plt
from core.config import MODEL_PATH, FEATURES_FILE, ALERTS_FILE, EXPLAIN_DIR

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

    os.makedirs(EXPLAIN_DIR, exist_ok=True)
    out_path = os.path.join(EXPLAIN_DIR, "shap_feature_importance.png")
    shap.summary_plot(shap_values, X.tail(n), plot_type="bar", show=False)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()

    print(f"✅ SHAP feature importance saved to {out_path}")

if __name__ == "__main__":
    explain_latest_alert(n=1)
