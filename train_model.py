import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)
import joblib

DB_PATH = "alerts.db"
MODEL_PATH = "model.pkl"


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT metric, value, hour, day_of_week, is_weekend, message_len, value_bucket, label
        FROM alerts
        WHERE label IN ('Critical','Noise')
    """, conn)
    conn.close()
    return df


def baseline_predict(records, threshold=80.0):
   
   
    preds = []
    for r in records:
        v = r.get("value", 0)
        if v is None:
            v = 0
        preds.append(1 if float(v) >= threshold else 0)
    return preds


def print_results(title, y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)
    print(f"Accuracy : {acc:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall   : {recall:.3f}")
    print(f"F1-Score : {f1:.3f}")

    print("\nConfusion Matrix (rows=true, cols=pred):")
    print(cm)

    print("\nClassification Report:")
    print(classification_report(
        y_true,
        y_pred,
        target_names=["Noise", "Critical"],
        zero_division=0
    ))


def compare_results(y_test, y_pred_ml, y_pred_base):
    ml_acc = accuracy_score(y_test, y_pred_ml)
    base_acc = accuracy_score(y_test, y_pred_base)

    ml_f1 = f1_score(y_test, y_pred_ml, zero_division=0)
    base_f1 = f1_score(y_test, y_pred_base, zero_division=0)

    print("\n" + "=" * 50)
    print("FINAL COMPARISON SUMMARY")
    print("=" * 50)
    print(f"ML Accuracy       : {ml_acc:.3f}")
    print(f"Baseline Accuracy : {base_acc:.3f}")
    print(f"ML F1-Score       : {ml_f1:.3f}")
    print(f"Baseline F1-Score : {base_f1:.3f}")

    if ml_acc > base_acc:
        print("\nML model performed better than the baseline based on accuracy.")
    elif ml_acc < base_acc:
        print("\n Baseline performed better than the ML model based on accuracy.")
    else:
        print("\nML model and baseline achieved the same accuracy.")


def main():
    df = load_data()

    if len(df) < 20:
        print("Not enough data to train well. Add at least 20 labelled alerts first.")
        return

    print(f"Total labelled alerts found: {len(df)}")

    label_counts = df["label"].value_counts()
    print("\nLabel distribution:")
    print(label_counts)

   
    X = df[[
        "metric",
        "value",
        "hour",
        "day_of_week",
        "is_weekend",
        "message_len",
        "value_bucket"
    ]].to_dict(orient="records")

   
    y = (df["label"] == "Critical").astype(int)

    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")

   
    model = Pipeline([
        ("vec", DictVectorizer(sparse=True)),
        ("clf", LogisticRegression(max_iter=500))
    ])

    model.fit(X_train, y_train)

   
    y_pred_ml = model.predict(X_test)

  
    y_pred_base = baseline_predict(X_test, threshold=80.0)

  
    print_results("ML MODEL RESULTS", y_test, y_pred_ml)
    print_results("BASELINE RULE RESULTS (value >= 80 -> Critical)", y_test, y_pred_base)

    
    compare_results(y_test, y_pred_ml, y_pred_base)

    
    joblib.dump(model, MODEL_PATH)
    print(f"\n Saved ML model to: {MODEL_PATH}")


if __name__ == "__main__":
    main()