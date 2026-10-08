"""
AquaTwin AI - Model Training Script
------------------------------------
Trains a Random Forest classifier on sensor readings to distinguish between
three cooling-system states: Normal, Evaporation, and Leak.

Features used:
    temp_c          - current temperature (deg C)
    humidity_pct    - current relative humidity (%)
    water_level_pct - current water level (%)
    delta_level     - change in water level since last reading (negative = drop)
    delta_humidity  - change in humidity since last reading

This uses a small, hand-crafted dataset for demo/prototype purposes.
For a production deployment, replace dataset/sensor_training_data.csv with
readings logged from the real hardware over many run cycles.
"""

import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset", "sensor_training_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "aquatwin_rf_model.joblib")

FEATURES = ["temp_c", "humidity_pct", "water_level_pct", "delta_level", "delta_humidity"]
LABEL = "label"


def main():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(df)

    X = df[FEATURES]
    y = df[LABEL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print("\nTraining Random Forest classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    print("\nEvaluating on held-out split:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"Accuracy on held-out split: {accuracy_score(y_test, y_pred):.2f}")

    print("\nFeature importances:")
    for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat:16s} {imp:.3f}")

    # Retrain on the full dataset before saving
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
