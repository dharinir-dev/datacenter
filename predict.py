"""
AquaTwin AI - Prediction Script
---------------------------------
Loads the trained Random Forest model and classifies a sensor reading as
Normal, Evaporation, or Leak, printing the recommended action for each.

Usage:
    python predict.py                        -> runs 3 built-in demo readings
    python predict.py 26.1 57 33 -21.0 0.3    -> classify a custom reading
                                                  (temp_c humidity_pct water_level_pct
                                                   delta_level delta_humidity)
"""

import os
import sys
import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "aquatwin_rf_model.joblib")
FEATURES = ["temp_c", "humidity_pct", "water_level_pct", "delta_level", "delta_humidity"]

RECOMMENDATIONS = {
    "Normal": (
        "System operating normally. Water level and humidity are within "
        "expected range. Continue standard operation."
    ),
    "Evaporation": (
        "Gradual water loss consistent with evaporation detected (slow level "
        "drop with rising humidity). Recommend activating the condensation "
        "recovery cycle."
    ),
    "Leak": (
        "Sudden water-level drop detected without the expected rise in "
        "humidity. Recognized as an abnormal leak signature. Recommend "
        "diverting the water flow and triggering the alert immediately."
    ),
}

DEMO_READINGS = [
    (25.1, 55, 79, 0.0, 0.2),       # expected: Normal
    (28.2, 66, 68, -2.1, 4.8),      # expected: Evaporation
    (26.1, 57, 33, -21.0, 0.3),     # expected: Leak
]


def classify(model, reading):
    row = pd.DataFrame([reading], columns=FEATURES)
    prediction = model.predict(row)[0]
    probabilities = dict(zip(model.classes_, model.predict_proba(row)[0]))
    return prediction, probabilities


def main():
    if not os.path.exists(MODEL_PATH):
        print("No trained model found. Run train_model.py first.")
        sys.exit(1)

    model = joblib.load(MODEL_PATH)

    if len(sys.argv) == 6:
        readings = [tuple(float(x) for x in sys.argv[1:6])]
    else:
        readings = DEMO_READINGS

    for reading in readings:
        prediction, probabilities = classify(model, reading)
        print("-" * 60)
        print(f"Reading: temp={reading[0]}C humidity={reading[1]}% level={reading[2]}% "
              f"d_level={reading[3]} d_humidity={reading[4]}")
        print(f"Predicted state: {prediction}")
        print("Confidence:", {k: round(v, 2) for k, v in probabilities.items()})
        print(f"Recommendation: {RECOMMENDATIONS[prediction]}")

    print("-" * 60)


if __name__ == "__main__":
    main()
