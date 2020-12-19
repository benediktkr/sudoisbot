#!/usr/bin/python3

from sudoisbot.sensors.sensors import ArduinoCurrentSensor

with ArduinoCurrentSensor(name="test", kind="arduino-current") as ard:
    for reading in ard.iter_lines():
        print(reading)
