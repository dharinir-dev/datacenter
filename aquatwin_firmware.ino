/*
  AquaTwin AI - Firmware (Arduino Uno)
  --------------------------------------
  STATUS: Written and ready for hardware bring-up. Not yet tested on
  physical hardware - pin assignments below are a starting point and
  may need adjustment once sensors are wired.

  Responsibilities:
    1. Read temperature/humidity (DHT11/DHT22) and water-level sensor
    2. Compute delta_level and delta_humidity since the last reading
    3. Print one CSV line per cycle over Serial for the ML layer:
         temp_c,humidity_pct,water_level_pct,delta_level,delta_humidity
    4. Run onboard rule-based classification as a fallback (works even
       without the laptop/ML layer connected)
    5. Listen for an optional serial override byte from the ML model:
         'N' = Normal   'E' = Evaporation   'L' = Leak
    6. Drive the LCD, status LEDs, buzzer, and pump relay accordingly

  Libraries required (install via Arduino Library Manager):
    - DHT sensor library (Adafruit)
    - LiquidCrystal_I2C

  TODO before hardware bring-up:
    - Confirm actual pin wiring matches the #define block below
    - Calibrate water-level sensor raw-value-to-percent mapping
    - Tune the threshold constants against real sensor noise
*/

#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------- Pin assignments (adjust to match actual wiring) ----------
#define DHTPIN 2
#define DHTTYPE DHT22
#define WATER_LEVEL_PIN A0
#define RELAY_PIN 8
#define LED_GREEN 5
#define LED_YELLOW 6
#define LED_RED 7
#define BUZZER_PIN 9

// ---------- Thresholds (placeholder - calibrate against real sensors) ----------
const float LEAK_DROP_THRESHOLD = -10.0;      // sudden level drop
const float EVAP_DROP_THRESHOLD = -0.8;       // gradual level drop
const float EVAP_HUMIDITY_RISE = 1.5;         // humidity rise expected with evaporation
const float LEAK_HUMIDITY_FLAT = 1.0;         // humidity considered "not rising"

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

float lastLevel = -1;
float lastHumidity = -1;

void setup() {
  Serial.begin(9600);
  dht.begin();
  lcd.init();
  lcd.backlight();

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, HIGH);  // relay HIGH = pump ON (adjust if wired inverted)

  lcd.setCursor(0, 0);
  lcd.print("AquaTwin AI");
  delay(1500);
}

float readWaterLevelPercent() {
  int raw = analogRead(WATER_LEVEL_PIN);
  // Placeholder linear mapping - replace with calibrated values
  // once the actual sensor's raw range is known.
  return constrain(map(raw, 0, 1023, 0, 100), 0, 100);
}

String classify(float level, float humidity, float dLevel, float dHumidity) {
  if (dLevel <= LEAK_DROP_THRESHOLD && dHumidity < LEAK_HUMIDITY_FLAT) {
    return "Leak";
  }
  if (dLevel <= EVAP_DROP_THRESHOLD && dHumidity >= EVAP_HUMIDITY_RISE) {
    return "Evaporation";
  }
  return "Normal";
}

void applyState(String state) {
  digitalWrite(LED_GREEN, state == "Normal" ? HIGH : LOW);
  digitalWrite(LED_YELLOW, state == "Evaporation" ? HIGH : LOW);
  digitalWrite(LED_RED, state == "Leak" ? HIGH : LOW);
  digitalWrite(BUZZER_PIN, state == "Leak" ? HIGH : LOW);
  digitalWrite(RELAY_PIN, state == "Leak" ? LOW : HIGH);  // cut pump on leak

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Status: " + state);
}

void loop() {
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();
  float level = readWaterLevelPercent();

  if (isnan(humidity) || isnan(temp)) {
    Serial.println("Sensor read error");
    delay(2000);
    return;
  }

  float dLevel = (lastLevel < 0) ? 0 : (level - lastLevel);
  float dHumidity = (lastHumidity < 0) ? 0 : (humidity - lastHumidity);
  lastLevel = level;
  lastHumidity = humidity;

  // 1) Send reading to the ML layer over Serial
  Serial.print(temp); Serial.print(",");
  Serial.print(humidity); Serial.print(",");
  Serial.print(level); Serial.print(",");
  Serial.print(dLevel); Serial.print(",");
  Serial.println(dHumidity);

  // 2) Onboard fallback classification
  String onboardState = classify(level, humidity, dLevel, dHumidity);
  String activeState = onboardState;

  // 3) Check for an ML override arriving over Serial
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'N') activeState = "Normal";
    else if (c == 'E') activeState = "Evaporation";
    else if (c == 'L') activeState = "Leak";
  }

  // 4) Drive outputs
  applyState(activeState);

  lcd.setCursor(0, 1);
  lcd.print("L:" + String((int)level) + "% H:" + String((int)humidity) + "%");

  delay(2000);
}
