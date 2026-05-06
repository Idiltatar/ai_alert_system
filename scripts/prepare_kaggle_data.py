import pandas as pd

input_path = "data/kaggle/archive (1)/GUIDE_Train.csv"
output_path = "data/kaggle/kaggle_alerts_prepared.csv"

print("Loading dataset...")

df = pd.read_csv(input_path, nrows=5000)

prepared = pd.DataFrame()

# Convert Kaggle columns into your alert system format
prepared["metric"] = df["Category"].fillna("UNKNOWN")

prepared["value"] = 100

prepared["message"] = df["AlertTitle"].fillna("No alert message")

prepared["timestamp"] = df["Timestamp"]

prepared["label"] = df["IncidentGrade"].map({
    "TruePositive": "Critical",
    "BenignPositive": "Noise",
    "FalsePositive": "Noise"
}).fillna("Noise")
print(prepared.head())

prepared.to_csv(output_path, index=False)

print("\nPrepared dataset saved.")
print("Output:", output_path)

print("\nLabel counts:")
print(prepared["label"].value_counts())