"""
AquaTwin AI - Serial Bridge (Arduino <-> ML model)
-----------------------------------------------------
NOT YET CONNECTED TO PHYSICAL HARDWARE - this is the integration point for
when the Arduino prototype is wired up and running firmware/aquatwin_firmware.ino.

Expected Arduino serial output (one line per reading, comma-separated):
    <temp_c>,<humidity_pct>,<water_level_pct>,<delta_level>,<delta_humidity>
    e.g.  26.1,57,33,-21.0,0.3

This script reads that line, classifies it with the trained model, and writes
a single character back to the Arduino:
    'N' = Normal   'E' = Evaporation   'L' = Leak

Requires: pip install pyserial
Update SERIAL_PORT to match your system (e.g. "COM5" on Windows,
"/dev/ttyACM0" on Linux, "/dev/cu.usbmodemXXXX" on Mac).
"""

import os
import time
import joblib
import pandas as pd
import serial

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "aquatwin_rf_model.joblib")
FEATURES = ["temp_c", "humidity_pct", "water_level_pct", "delta_level", "delta_humidity"]

SERIAL_PORT = "COM5"   # <-- change this once hardware is connected
BAUD_RATE = 9600

LABEL_TO_CODE = {"Normal": "N", "Evaporation": "E", "Leak": "L"}


def main():
    model = joblib.load(MODEL_PATH)
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # allow Arduino to reset after serial connect

    print(f"Listening on {SERIAL_PORT}... (Ctrl+C to stop)")
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        try:
            values = [float(x) for x in line.split(",")]
            if len(values) != len(FEATURES):
                print(f"Ignoring malformed line: {line}")
                continue
        except ValueError:
            print(f"Ignoring malformed line: {line}")
            continue

        row = pd.DataFrame([values], columns=FEATURES)
        prediction = model.predict(row)[0]
        code = LABEL_TO_CODE[prediction]

        print(f"Reading: {values} -> {prediction}")
        ser.write(code.encode("utf-8"))


if __name__ == "__main__":
    main()
