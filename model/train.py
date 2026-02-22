import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

FEATURES_FILE = "data/features_advanced.csv"
MODEL_PATH = "model/ids_model.pkl"

df = pd.read_csv(FEATURES_FILE)
X = df.drop(columns=[c for c in ["time", "src_ip"] if c in df.columns])

model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
model.fit(X)

joblib.dump(model, MODEL_PATH)
print("✅ Model trained and saved to model/ids_model.pkl")
