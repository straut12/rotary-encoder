from machine import Pin
from time import sleep
import ujson
from rotaryencoder import RotaryEncoder

if __name__ == "__main__":
    
  micropython.alloc_emergency_exception_buf(100) # allow reporting of exception errors in ISR

  def on_message(topic, msg):
    #print("Topic %s msg %s ESP Subscribed to %s" % (topic, msg, MQTT_SUB_TOPIC1))
    global newmsg, incomingD
    if topic == MQTT_SUB_TOPIC1:
      incomingD = ujson.loads(msg.decode("utf-8", "ignore")) # decode json data to dictionary
      newmsg = True
      #Uncomment prints for debugging. Will print the JSON incoming payload and unpack the converted dictionary
      #print("Received topic(tag): {0}".format(topic))
      #print("JSON payload: {0}".format(msg.decode("utf-8", "ignore")))
      #print("Unpacked dictionary (converted JSON>dictionary)")
      #for key, value in incomingD.items():
      #  print("{0}:{1}".format(key, value))
      
  def connect_and_subscribe():
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_SUB_TOPIC1
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PASSWORD)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(MQTT_SUB_TOPIC1)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (MQTT_SERVER, MQTT_SUB_TOPIC1))
    return client

  def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    sleep(10)
    machine.reset()

  try:
    mqtt_client = connect_and_subscribe()
  except OSError as e:
    restart_and_reconnect()

  def is_integer(n):
      if n == None or n == "na":
          return False
      if isinstance(n, int):
        return True
      if abs(round(n) - n) == 0.5:
        return False
      else:
        return True

  # MQTT setup is successful.
  # Publish generic status confirmation easily seen on MQTT Explorer
  # Initialize dictionaries and start the main loop.
  mqtt_client.publish(b"status", b"esp32 connected, entering main loop")
  led = Pin(2, Pin.OUT) #2 is the internal LED
  led.value(1)
  sleep(1)
  led.value(0)  # flash led to know main loop starting
  
  outgoingD, incomingD = {}, {}
  newmsg = True
  clkPin, dtPin, button = 18, 5, 4
  rotEnc1 = RotaryEncoder(clkPin, dtPin, button)

  while True:
      try:
        mqtt_client.check_msg()
        if newmsg:                 # Place holder if wanting to receive message/instructions
          newmsg = False
        clicks, buttonstate = rotEnc1.runencoder()
        if is_integer(clicks):
            outgoingD = {"RotEnc1Ci":str(clicks), "RotEnc1Bi":str(buttonstate)}
            print("clicks: {0} Button: {1}".format(clicks, buttonstate))
            mqtt_client.publish(MQTT_PUB_TOPIC1, ujson.dumps(outgoingD))  # Convert to JSON and publish voltage of each channel
            #Uncomment prints for debugging. 
            print(ujson.dumps(outgoingD))
            #print("JSON payload: {0}\n".format(ujson.dumps(outgoingD)))
      except OSError as e:
        restart_and_reconnect()