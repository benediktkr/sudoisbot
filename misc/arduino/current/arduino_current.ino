






/*
** !
 * @file readACCurrent.
 * @n This example reads Analog AC Current Sensor.

 * @copyright   Copyright (c) 2010 DFRobot Co.Ltd (https://www.dfrobot.com)
 * @licence     The MIT License (MIT)
 * @get from https://www.dfrobot.com

 Created 2016-3-10
 By berinie Chen <bernie.chen@dfrobot.com>

 Revised 2019-8-6
 By Henry Zhao<henry.zhao@dfrobot.com>
*/

long timeout;
long initial_timeout = 300000;

const int ACPin = A2;         //set arduino signal read pin
#define ACTectionRange 20;    //set Non-invasive AC Current Sensor tection range (5A,10A,20A)

// VREF: Analog reference
// For Arduino UNO, Leonardo and mega2560, etc. change VREF to 5
// For Arduino Zero, Due, MKR Family, ESP32, etc. 3V3 controllers, change VREF to 3.3
#define VREF 5.0

float read_sensor()
{
  float ACCurrtntValue = 0;
  float peakVoltage = 0;
  float voltageVirtualValue = 0;  //Vrms
  for (int i = 0; i < 5; i++)
  {
    peakVoltage += analogRead(ACPin);   //read peak voltage
    delay(1);
  }
  peakVoltage = peakVoltage / 5;
  voltageVirtualValue = peakVoltage * 0.707;    //change the peak voltage to the Virtual Value of voltage

  /*The circuit is amplified by 2 times, so it is divided by 2.*/
  voltageVirtualValue = (voltageVirtualValue / 1024 * VREF ) / 2;

  ACCurrtntValue = voltageVirtualValue * ACTectionRange;

  return ACCurrtntValue;
}

void setup()
{
  pinMode(13, OUTPUT);
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

void loop()
{
  if (timeout != 0) {
    print_value();
    delay(timeout);

    // ?
    digitalWrite(13, HIGH);
    delay(500);
    digitalWrite(13, LOW);
    delay(500);
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

void print_value() {
  float val = read_sensor(); //read AC Current Value
  String json = "{"
    "\"value\": " + String(val) + ", " +
    "\"timeout\": " + String(timeout) + ", " +
    "\"on_fire\": false" +
  "}";
  Serial.println(json);
}
