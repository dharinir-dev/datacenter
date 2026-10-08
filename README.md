# AquaTwin AI

**Water-loss early warning, recovery and reuse system for cooling infrastructure.**

AquaTwin AI monitors a water-based cooling loop, detects abnormal water loss, and distinguishes *why* the water is dropping: normal operation, gradual evaporation, or a sudden leak. Unlike simple threshold alarms, it classifies the state from multiple sensor signals using a Random Forest model and recommends an action (continue, start condensation recovery, or cut the pump and alert).

> **Project status:** The software stack (ML classifier, decision logic, hardware-free simulator, Arduino firmware) is complete. Physical hardware integration is in progress. The firmware is written but not yet validated on a wired prototype, and the model is trained on a small hand-crafted dataset (see Limitations).

## Core idea

```
Monitor -> Detect -> Decide -> Protect -> Recover -> Reuse
```

| State | Sensor signature | Recommended action |
|---|---|---|
| Normal | Level and humidity stable | Continue operation |
| Evaporation | Gradual level drop, humidity rising | Start condensation recovery cycle |
| Leak | Sudden level drop, humidity flat | Cut pump, sound alert, divert flow |

## Repository structure

```
aquatwin-ai/
├── ml/
│   ├── dataset/sensor_training_data.csv   # small training dataset (18 rows, 3 classes)
│   ├── train_model.py                     # trains and saves the Random Forest
│   ├── predict.py                         # classify a reading, print recommendation
│   └── serial_bridge.py                   # Arduino <-> model link (for hardware phase)
├── simulation/
│   └── simulate_demo.py                   # hardware-free end-to-end demo
├── firmware/
│   └── aquatwin_firmware.ino              # Arduino Uno sketch (pending hardware validation)
├── requirements.txt
└── LICENSE
```

## Quick start (no hardware needed)

```bash
git clone https://github.com/<your-username>/aquatwin-ai.git
cd aquatwin-ai
pip install -r requirements.txt

python ml/train_model.py           # train and save the model
python simulation/simulate_demo.py # run the full simulated scenario
python ml/predict.py 26.1 57 33 -21.0 0.3   # classify a custom reading
```

Custom reading arguments: `temp_c humidity_pct water_level_pct delta_level delta_humidity`.

## How it works

**Features (per reading):** temperature, humidity, water level, change in level since last reading, change in humidity since last reading.

**Model:** `RandomForestClassifier` (100 trees, max depth 4), a supervised multi-class classifier. It was chosen because it handles small, noisy tabular sensor data well, needs no feature scaling, returns confidence scores, and exposes feature importances for explainability.

**Simulation:** `simulate_demo.py` generates a scripted stream (normal, then evaporation, then recovery, then a sudden leak), runs every reading through the trained model, and prints the predicted state, confidence, and the action the hardware would take (relay off, buzzer, LED).

## Hardware plan (in progress)

- Arduino Uno, DHT22 temperature/humidity sensor, water-level sensor
- Relay-controlled aquarium pump, LCD, status LEDs, buzzer
- Condensation-based recovery stage and optional solar-powered control unit
- `firmware/aquatwin_firmware.ino` reads sensors, streams CSV over serial, runs a rule-based fallback, and accepts a one-byte override (`N`/`E`/`L`) from `serial_bridge.py`

## Limitations (honest scope)

- The training dataset is small and hand-crafted; the model has not yet seen real sensor data. Next step: log readings from the physical rig and retrain.
- Firmware thresholds and pin mappings are placeholders until calibrated on hardware.
- Reported accuracy on the held-out split reflects the tiny dataset and should not be read as real-world performance.

## Roadmap

- [ ] Wire up hardware and validate firmware
- [ ] Collect real sensor logs and retrain
- [ ] Live dashboard (Streamlit) for readings and confidence
- [ ] Time-series model for leak forecasting
- [ ] Multi-zone monitoring

## License

MIT
