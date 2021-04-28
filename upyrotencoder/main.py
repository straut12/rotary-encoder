import utime, ubinascii, micropython, network, re, ujson
from lib.umqttsimple import MQTTClient
from machine import Pin
from rotaryencoder import RotaryEncoder  # Import RotaryEncoder module created in /lib folder
import gc
gc.collect()
micropython.alloc_emergency_exception_buf(100)

def connect_wifi(WIFI_SSID, WIFI_PASSWORD):
    station = network.WLAN(network.STA_IF)

    station.active(True)
    station.connect(WIFI_SSID, WIFI_PASSWORD)

    while station.isconnected() == False:
        pass

    print('Connection successful')
    print(station.ifconfig())

def mqtt_setup(IPaddress):
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_REGEX
    with open("stem", "rb") as f:    # Remove and over-ride MQTT/WIFI login info below
      stem = f.read().splitlines()
    MQTT_SERVER = IPaddress   # Over ride with MQTT/WIFI info
    MQTT_USER = stem[0]         
    MQTT_PASSWORD = stem[1]
    WIFI_SSID = stem[2]
    WIFI_PASSWORD = stem[3]
    MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
    MQTT_SUB_TOPIC = b'esp32/rotenc/instructions'   # Place holder. No instructions are sent from nodered to rot encoder
    
def mqtt_connect_subscribe():
    global MQTT_CLIENT_ID, MQTT_SERVER, MQTT_SUB_TOPIC, MQTT_USER, MQTT_PASSWORD
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, user=MQTT_USER, password=MQTT_PASSWORD)
    client.set_callback(mqtt_on_message)
    client.connect()
    print('(CONNACK) Connected to {0} MQTT broker'.format(MQTT_SERVER))
    client.subscribe(MQTT_SUB_TOPIC)
    print('Subscribed to {0}'.format(MQTT_SUB_TOPIC))
    return client

def mqtt_on_message(topic, msg):
    print("on_message Received - topic:{0} payload:{1}".format(topic, msg.decode("utf-8", "ignore")))
    # No messages sent for encoder in this project

def mqtt_reset():
    print('Failed to connect to MQTT broker. Reconnecting...')
    utime.sleep_ms(5000)
    machine.reset()
    
# A rotary encoder function is not necessary but will be useful later for scalibility.
# Eventually want to incorporate ADC, rotary encoder, servo, motors, etc in one program so pays off to
# setup a structure early on. This will make it easier to add devices later.

def create_rotary_encoder(clkPin, dtPin, button_rotenc):
    ''' Setup the rotary encoder items needed to publish knob status to node red '''
    global pinsummary, device, outgoingD
    device.append(b'rotencoder')
    outgoingD[b'rotencoder'] = {}
    outgoingD[b'rotencoder']['data'] = {}
    outgoingD[b'rotencoder']['send'] = False   # Used to flag when to send results
    pinsummary.append(clkPin)
    pinsummary.append(dtPin)
    if button_rotenc is not None: pinsummary.append(button_rotenc)
    return RotaryEncoder(clkPin, dtPin, button_rotenc, setupinfo=True, debuginfo=False)

def main():
    global pinsummary          # Will keep track of what pins are being used to help avoid duplicates
    global device, outgoingD   # Containers setup in 'create' functions and used for Publishing mqtt
    
    #===== SETUP MQTT/DEBUG VARIABLES ============#
    # Setup mqtt variables (topics and data containers) used in on_message, main loop, and publishing
    # Further setup of variables is completed in specific 'create_device' functions
    mqtt_setup('10.0.0.115')
    device = []    # mqtt lvl2 topic category and '.appended' in create functions
    outgoingD = {} # container used for publishing mqtt data
    
    # umqttsimple requires topics to be byte format. For string.join to work on topics, all items must be the same, bytes.
    ESPID = b'/esp32A'  # Specific MQTT_PUB_TOPICS created at time of publishing using string.join (specifically lvl2.join)
    MQTT_PUB_TOPIC = [b'esp2nred/', ESPID]
  
    # Used to stagger timers for checking msgs, getting data, and publishing msgs
    on_msgtimer_delay_ms = 250
    
    #=== SETUP DEVICES ===#
    # Boot fails if pin 12 is pulled high
    # Pins 34-39 are input only and do not have internal pull-up resistors. Good for ADC
    # Items that are sent as part of mqtt topic will be binary (b'item)
    pinsummary = []
    
    clkPin, dtPin, button_rotenc = 15, 4, 2
    rotEnc1 = create_rotary_encoder(clkPin, dtPin, button_rotenc)
    
    print('Pins in use:{0}'.format(sorted(pinsummary)))
    #==========#
    # Connect and create the client
    try:
        mqtt_client = mqtt_connect_subscribe()
    except OSError as e:
        mqtt_reset()
    # MQTT setup is successful, publish status msg and flash on-board led
    mqtt_client.publish(b'status'.join(MQTT_PUB_TOPIC), b'esp32 connected, entering main loop')

    sendmsgs = False    
   
    while True:
        try:
            clicks = rotEnc1.update()
            if clicks is not None:
                outgoingD[b'rotencoder']['send'] = True
                outgoingD[b'rotencoder']['data']['RotEnc1Ci'] = str(clicks[0])
                outgoingD[b'rotencoder']['data']['RotEnc1Bi'] = str(clicks[1]) # Button state
                sendmsgs = True

            if sendmsgs:
                item = b'rotencoder'
                if outgoingD[item]['send']:
                    mqtt_client.publish(item.join(MQTT_PUB_TOPIC), ujson.dumps(outgoingD[item]['data']))
                    print('Published msg {0} with payload {1}'.format(item.join(MQTT_PUB_TOPIC), ujson.dumps(outgoingD[item]['data'])))
                    outgoingD[item]['send'] = False
                sendmsgs = False
                
        except OSError as e:
            mqtt_reset()

if __name__ == "__main__":
    # Run main loop            
    main()
