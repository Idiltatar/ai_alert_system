import pandas as pd

path = "data/kaggle/kaggle_alerts_prepared.csv"

df = pd.read_csv(path)

print("Kaggle prepared dataset loaded successfully")
print("Total rows:", len(df))

print("\nColumns:")
print(df.columns.tolist())

print("\nLabel distribution:")
print(df["label"].value_counts())

print("\nMetric distribution:")
print(df["metric"].value_counts().head(10))

print("\nSample rows:")
print(df.head(10))