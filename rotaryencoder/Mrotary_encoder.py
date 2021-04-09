#!/usr/bin/env python3
import RPi.GPIO as GPIO

class RotaryEncoder:
  def __init__(self, clkPin, dtPin):
    self.clkPin = clkPin
    self.dtPin = dtPin
    self.counter = 0
    self.clkUpdate = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.clkPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(self.dtPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    self.clkLastState = GPIO.input(self.clkPin)
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)

  def runencoder(self):
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)
    if self.clkState != self.clkLastState:
      if self.dtState != self.clkState:
        self.counter -= 0.5
      else:
        self.counter += 0.5
      #print(self.counter)
      self.clkLastState = self.clkState
      return self.counter

if __name__ == "__main__":
  clkPin = 17
  dtPin = 27
  rotEnc1 = RotaryEncoder(clkPin, dtPin)
  while True:
    clicks = rotEnc1.runencoder()

