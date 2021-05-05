#!/usr/bin/env python3
'''
Pass the pins the clk/dt and button are connected to. Records the position of the button
both CW and CCW. Starts at 0 and increments by 1 or -1.

Returns two integers: (1) the position of the knob and (2) the state of the button, 0 or 1.

'''

import logging
import RPi.GPIO as GPIO

class RotaryEncoder:
  def __init__(self, clkPin, dtPin, button, key1='RotEnc1Ci', key2='RotEnc1Bi', setupinfo=True):
    self.clkPin = clkPin
    self.dtPin = dtPin
    self.button = button
    self.counter = 0
    self.clkUpdate = True
    self.buttonpressed = False
    self.outgoing = [0,0]
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.clkPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(self.dtPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    self.clkLastState = GPIO.input(self.clkPin)
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)
    GPIO.add_event_detect(self.button, GPIO.BOTH, callback=self._button_callback)
    if setupinfo: print('Rotary Encoder pins- clk:{0} data:{1} button:{2}'.format(self.clkPin, self.dtPin, self.button))

  def runencoder(self):
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)
    if self.clkState != self.clkLastState or self.buttonpressed:
      if self.clkState != self.clkLastState:
        if self.dtState != self.clkState:
          self.counter -= 0.5
        else:
          self.counter += 0.5
        self.clkLastState = self.clkState
      buttonstate = GPIO.input(self.button)
      self.buttonpressed = False
      if self._is_integer(self.counter):
        self.outgoing[0] = self.counter
        self.outgoing[1] = buttonstate
        return self.outgoing

  def cleanupGPIO(self):
    GPIO.cleanup()
  
  def _button_callback(self, channel):
    self.buttonpressed = True

  def _is_integer(self, n):
        if n == None:
            return False
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

  ''' alternative integer check
  def is_integer_num(n):
      if isinstance(n, int):
          return True
      if isinstance(n, float):
          return n.is_integer()
      return False
  '''

if __name__ == "__main__":
  
  logging.basicConfig(level=logging.DEBUG) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
  logging.info("GPIO version: {0}".format(GPIO.VERSION))

  clkPin = 17              # Using BCM GPIO number for pins
  dtPin = 27
  button = 24
  rotEnc1 = RotaryEncoder(clkPin, dtPin, button)
  
  try:
    while True:
      clicks = rotEnc1.runencoder()
      if clicks is not None:
        logging.debug("clicks:{0}".format(clicks))
  except KeyboardInterrupt:
    logging.info("Pressed ctrl-C")
  finally:
    rotEnc1.cleanupGPIO()
    logging.info("GPIO cleaned up")

