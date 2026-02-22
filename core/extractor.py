import pandas as pd
import numpy as np
from scipy.stats import entropy
from sklearn.preprocessing import StandardScaler
from core.config import TRAFFIC_FILE, FEATURES_FILE, WINDOW_SIZE

def shannon_entropy(series):
    probs = series.value_counts(normalize=True)
    return entropy(probs, base=2)

def extract_advanced_features(input_file=TRAFFIC_FILE, output_file=FEATURES_FILE):
    df = pd.read_csv(input_file)

    # Convert time to datetime
    df["time"] = pd.to_datetime(df["time"])

    # Inter-arrival time
    df = df.sort_values(by=["src_ip", "time"])
    df["inter_arrival"] = df.groupby("src_ip")["time"].diff().dt.total_seconds().fillna(0)

    # Time window aggregation
    df.set_index("time", inplace=True)
    grouped = df.groupby([pd.Grouper(freq=WINDOW_SIZE), "src_ip"])

    features = grouped.agg(
        packet_count=("size", "count"),
        avg_packet_size=("size", "mean"),
        std_packet_size=("size", "std"),
        max_packet_size=("size", "max"),
        min_packet_size=("size", "min"),
        avg_inter_arrival=("inter_arrival", "mean"),
        max_inter_arrival=("inter_arrival", "max"),
        unique_protocols=("protocol", "nunique"),
        unique_dst_ports=("dst_port", "nunique"),
    ).reset_index()

    # Entropy features
    proto_entropy = grouped["protocol"].apply(shannon_entropy).reset_index(name="protocol_entropy")
    port_entropy = grouped["dst_port"].apply(shannon_entropy).reset_index(name="port_entropy")

    features = features.merge(proto_entropy, on=["time", "src_ip"])
    features = features.merge(port_entropy, on=["time", "src_ip"])

    features.fillna(0, inplace=True)

    # Scaling
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    scaler = StandardScaler()
    features[numeric_cols] = scaler.fit_transform(features[numeric_cols])

    # Memory optimization: cap CSV size
    MAX_ROWS = 5000  # keep last 5000 windows only
    if len(features) > MAX_ROWS:
        features = features.tail(MAX_ROWS)

    features.to_csv(output_file, index=False)
    print("✅ Advanced features extracted and scaled!")
    return features

if __name__ == "__main__":
    extract_advanced_features()
