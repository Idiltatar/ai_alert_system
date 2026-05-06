import os
import pandas as pd

folder = "data/kaggle/archive (1)"

print("Files in Kaggle folder:")
print(os.listdir(folder))

for file in os.listdir(folder):
    if file.endswith(".csv"):
        path = os.path.join(folder, file)
        df = pd.read_csv(path, nrows=5)

        print("\nFILE:", file)
        print("Columns:")
        print(df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())