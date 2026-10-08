"""
AquaTwin AI - Standalone Simulation Demo
--------------------------------------------
Runs the full AquaTwin AI decision pipeline WITHOUT any physical hardware.
Generates a realistic stream of synthetic sensor readings that cycles through
Normal -> Evaporation -> Leak scenarios, feeds each one through the trained
Random Forest model, and prints a live "kiosk-style" status readout.

This lets the project be demonstrated end-to-end (sensing -> classification
-> recommended action) purely in software, ahead of physical sensor/Arduino
integration.

Usage:
    python simulate_demo.py
    python simulate_demo.py --speed 0.5     (seconds between readings, default 1.5)
"""

import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))

import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "aquatwin_rf_model.joblib")
FEATURES = ["temp_c", "humidity_pct", "water_level_pct", "delta_level", "delta_humidity"]

RECOMMENDATIONS = {
    "Normal": "System operating normally. Continue standard operation.",
    "Evaporation": "Gradual evaporation detected. Recommend activating condensation recovery cycle.",
    "Leak": "Sudden leak detected. Diverting water flow and triggering alert. Pump OFF.",
}

STATUS_ICON = {"Normal": "[OK]", "Evaporation": "[!]", "Leak": "[ALERT]"}


def generate_reading(state, level):
    """Generate one synthetic sensor reading for the given scenario state."""
    if state == "Normal":
        temp = round(random.uniform(24.5, 25.5), 1)
        humidity = round(random.uniform(53, 58), 0)
        d_level = round(random.uniform(-0.3, 0.3), 1)
        d_humidity = round(random.uniform(-0.3, 0.5), 1)
    elif state == "Evaporation":
        temp = round(random.uniform(27, 29), 1)
        humidity = round(random.uniform(60, 70), 0)
        d_level = round(random.uniform(-3.0, -1.0), 1)
        d_humidity = round(random.uniform(2.5, 6.0), 1)
    else:  # Leak
        temp = round(random.uniform(25.5, 26.5), 1)
        humidity = round(random.uniform(54, 58), 0)
        d_level = round(random.uniform(-25.0, -15.0), 1)
        d_humidity = round(random.uniform(-0.5, 1.0), 1)

    level = max(0, min(100, level + d_level))
    return {
        "temp_c": temp,
        "humidity_pct": humidity,
        "water_level_pct": round(level, 1),
        "delta_level": d_level,
        "delta_humidity": d_humidity,
    }, level


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=1.5, help="seconds between readings")
    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print("No trained model found. Run ml/train_model.py first.")
        sys.exit(1)

    model = joblib.load(MODEL_PATH)

    # Scripted scenario: run normal for a while, drift into evaporation,
    # recover, then simulate a sudden leak.
    scenario = (
        ["Normal"] * 5
        + ["Evaporation"] * 5
        + ["Normal"] * 3
        + ["Leak"] * 4
    )

    level = 80.0
    print("=" * 70)
    print(" AquaTwin AI - Live Simulation (no hardware connected)")
    print("=" * 70)

    for i, state in enumerate(scenario, start=1):
        reading, level = generate_reading(state, level)
        row = pd.DataFrame([reading], columns=FEATURES)
        prediction = model.predict(row)[0]
        confidence = dict(zip(model.classes_, model.predict_proba(row)[0]))

        print(f"\n[{i:02d}] temp={reading['temp_c']}C  humidity={reading['humidity_pct']}%  "
              f"level={reading['water_level_pct']}%  "
              f"(d_level={reading['delta_level']}, d_humidity={reading['delta_humidity']})")
        print(f"     {STATUS_ICON[prediction]} Predicted: {prediction}  "
              f"(confidence: {round(confidence[prediction], 2)})")
        print(f"     Action: {RECOMMENDATIONS[prediction]}")

        if prediction == "Leak":
            print("     >> Simulated relay OFF, buzzer ON, red LED ON")
            level = min(100, level + 20)  # simulate a manual refill/reset after leak response

        time.sleep(args.speed)

    print("\n" + "=" * 70)
    print(" Simulation complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
