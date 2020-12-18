// based on https://lastminuteengineers.com/rain-sensor-arduino-tutorial/

// Sensor pins
#define sensorPower 7
#define sensorPin 8

long timeout;
long initial_timeout = 300000;

void setup() {
  pinMode(sensorPower, OUTPUT);
  pinMode(sensorPin, INPUT);

  // Initially keep the sensor OFF
  digitalWrite(sensorPower, LOW);

  Serial.begin(9600);

  // wait 5 minutes for the other side to tell us what the timeout should be
  Serial.setTimeout(initial_timeout);

  // signal we are ready to recieve the timeout value
  Serial.println("{\"ready\": true }");

  // block until we get the timeout value. since we power on the pin for the
  // raindrop sensor when we take the measurement, we dont want it looping
  // needlessly when nothing is reading because it corrodes when theres
  // voltage on the sensor.
  timeout = Serial.parseInt();
  Serial.setTimeout(timeout);
}

void loop() {
  if (timeout != 0) {
    int val = read_sensor();
    String digital;
    if (val == 1) {
      digital = "HIGH";
    }
    else {
      // water on the rain sensor, resistance has been LOWered
      digital = "LOW";
    }

    String json = "{"
        "\"digital\": \"" + digital + "\", " +
        "\"timeout\": " + String(timeout) +
      "}";
    Serial.println(json);

    delay(timeout);
  }
  else {
    String error = "{"
      "\"error\": \"timeout value was not sent in time\", "
      "\"timeout\": " + String(initial_timeout) +
    "}";
    Serial.println(error);

    // print it again every 60 seconds
    delay(60000);
  }

}

int read_sensor() {
  // when the amount of water exceeds the threshold value:
  // - status LED lights up
  // - digital output (DO) returns LOW.
  // - water LOWers resistence

  digitalWrite(sensorPower, HIGH);
  // Allow power to settle
  delay(10);
  int val = digitalRead(sensorPin);
  digitalWrite(sensorPower, LOW);
  return val;
}
