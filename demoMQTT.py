#!/usr/bin/env python3
# This MCP3008 adc is multi channel.  If any channel has a delta (current-previous) that is above the
# noise threshold then the voltage from all channels will be returned.
# MQTT version has a publish section in the main code to test MQTT ability stand alone
import sys, json, logging, re
from time import sleep
import paho.mqtt.client as mqtt
from os import path
from pathlib import Path
from logging.handlers import RotatingFileHandler
import rotaryencoder

if __name__ == "__main__":

    def is_integer(n):  # only record full clicks or increments of 1. Output is float (ie 1.0) so use is_integer()
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
    #==== LOGGING/DEBUGGING SETUP ============#

    def setup_logging(log_dir):
        # Create loggers
        main_logger = logging.getLogger(__name__)
        main_logger.setLevel(logging.INFO)
        log_file_format = logging.Formatter("[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(pathname)s:%(lineno)d")
        log_console_format = logging.Formatter("[%(levelname)s]: %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_console_format)

        exp_file_handler = RotatingFileHandler('{}/exp_debug.log'.format(log_dir), maxBytes=10**6, backupCount=5) # 1MB file
        exp_file_handler.setLevel(logging.INFO)
        exp_file_handler.setFormatter(log_file_format)

        exp_errors_file_handler = RotatingFileHandler('{}/exp_error.log'.format(log_dir), maxBytes=10**6, backupCount=5)
        exp_errors_file_handler.setLevel(logging.WARNING)
        exp_errors_file_handler.setFormatter(log_file_format)

        main_logger.addHandler(console_handler)
        main_logger.addHandler(exp_file_handler)
        main_logger.addHandler(exp_errors_file_handler)
        return main_logger
    
    # Can comment/uncomment to switch between the two methods of logging
    #basicConfig root logger
    logging.basicConfig(level=logging.DEBUG)                      # Can comment/uncomment to switch
    logging.info("Setup with basicConfig root logger")

    # getLogger (includes file logging)
    #logging = setup_logging(path.dirname(path.abspath(__file__)))  # Can comment/uncomment to switch
    #logging.info("Setup with getLogger console/file logging module")                      

    def on_connect(client, userdata, flags, rc):
        """ on connect callback verifies a connection established and subscribe to TOPICs"""
        global MQTT_SUB_TOPIC
        logging.info("attempting on_connect")
        if rc==0:
            mqtt_client.connected = True
            for topic in MQTT_SUB_TOPIC:
                client.subscribe(topic)
                logging.info("Subscribed to: {0}\n".format(topic))
            logging.info("Successful Connection: {0}".format(str(rc)))
        else:
            mqtt_client.failed_connection = True  # If rc != 0 then failed to connect. Set flag to stop mqtt loop
            logging.info("Unsuccessful Connection - Code {0}".format(str(rc)))

    def on_message(client, userdata, msg):
        """on message callback will receive messages from the server/broker. Must be subscribed to the topic in on_connect"""
        global incomingID, mqtt_dummy1, mqtt_dummy2
        logging.debug("Received: {0} with payload: {1}".format(msg.topic, str(msg.payload)))
        msgmatch = re.match(MQTT_REGEX, msg.topic)   # Check for match to subscribed topics
        if msgmatch:
            incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore"))) 
            incomingID = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(incomingD)] # breaks msg topic into groups - group/group1/group2
            if incomingID[2] == 'group2A':
                mqtt_dummy1 = incomingD
            elif incomingID[2] == 'group2B':
                mqtt_dummy2 = incomingD
        # Debugging. Will print the JSON incoming payload and unpack it
        logging.debug("Topic grp0:{0} grp1:{1} grp2:{2}".format(msgmatch.group(0), msgmatch.group(1), msgmatch.group(2)))
        incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore")))
        logging.debug("Payload type:{0}".format(type(incomingD)))
        if isinstance(incomingD, (str, bool, int, float)):
            logging.debug(incomingD)
        elif isinstance(incomingD, list):
            for item in incomingD:
                logging.debug(item)
        elif isinstance(incomingD, dict):
            for key, value in incomingD.items():  
                logging.debug("{0}:{1}".format(key, value))

    def on_publish(client, userdata, mid):
        """on publish will send data to client"""
        #Debugging. Will unpack the dictionary and then the converted JSON payload
        logging.debug("msg ID: " + str(mid)) 
        logging.debug("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
        for key, value in outgoingD.items():
            logging.debug("{0}:{1}".format(key, value))
        logging.debug("Converted msg published on topic: {0} with JSON payload: {1}\n".format(MQTT_PUB_TOPIC1, json.dumps(outgoingD))) # Uncomment for debugging. Will print the JSON incoming msg
        pass 

    def on_disconnect(client, userdata,rc=0):
        logging.debug("DisConnected result code "+str(rc))
        mqtt_client.loop_stop()

    #==== HARDWARE SETUP ===============#
    # Using BCM GPIO number for pins
    clkPin, dtPin, button = 17, 27, 24
    rotEnc1 = rotaryencoder.RotaryEncoder(clkPin, dtPin, button)
    
    home = str(Path.home())                       # Import mqtt and wifi info. Remove if hard coding in python script
    with open(path.join(home, "stem"),"r") as f:
        user_info = f.read().splitlines()

    #=======   MQTT SETUP ==============#
    MQTT_SERVER = '10.0.0.115'                    # Replace with IP address of device running mqtt server/broker
    MQTT_USER = user_info[0]                      # Replace with your mqtt user ID
    MQTT_PASSWORD = user_info[1]                  # Replace with your mqtt password

    MQTT_SUB_TOPIC = []          # + is wildcard for that level. Can .append more topics
    MQTT_SUB_TOPIC.append('nred2pi/rotencoderZCMD/+')
    #MQTT_SUB_TOPIC.append('nred2pi/stepperZCMD/+')
    #MQTT_SUB_TOPIC.append('nred2pi/servoZCMD/+')
    MQTT_REGEX = r'nred2pi/([^/]+)/([^/]+)'

    MQTT_CLIENT_ID = 'RPi4Argon1'

    #MQTT_PUB_TOPIC = 'pi2nred/stepperZDATA/'
    #MQTT_PUB_TOPIC = 'pi2nred/stepperZDATA/'
    #MQTT_PUB_TOPIC = 'pi2nred/stepperZDATA/'
    MQTT_PUB_TOPIC = 'pi2nred/rotencoderZDATA/'
    MQTT_PUB_TOPIC1 = MQTT_PUB_TOPIC + MQTT_CLIENT_ID

    #MQTT_PUB_TOPIC2 = 'pi2nred/nredZCMD/resetstepgauge'

    #==== START/BIND MQTT FUNCTIONS ====#
    # Create a couple flags to handle a failed attempt at connecting. If user/password is wrong we want to stop the loop.
    mqtt.Client.connected = False          # Flag for initial connection (different than mqtt.Client.is_connected)
    mqtt.Client.failed_connection = False  # Flag for failed initial connection
    # Create our mqtt_client object and bind/link to our callback functions
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
    mqtt_client.on_connect = on_connect    # Bind on connect
    mqtt_client.on_disconnect = on_disconnect             # Bind on disconnect
    mqtt_client.on_message = on_message    # Bind on message
    mqtt_client.on_publish = on_publish    # Bind on publish
    logging.info("Connecting to: {0}".format(MQTT_SERVER))
    mqtt_client.connect(MQTT_SERVER, 1883) # Connect to mqtt broker. This is a blocking function. Script will stop while connecting.
    mqtt_client.loop_start()               # Start monitoring loop as asynchronous. Starts a new thread and will process incoming/outgoing messages.
    # Monitor if we're in process of connecting or if the connection failed
    while not mqtt_client.connected and not mqtt_client.failed_connection:
        logging.info("Waiting")
        sleep(1)
    if mqtt_client.failed_connection:      # If connection failed then stop the loop and main program. Use the rc code to trouble shoot
        mqtt_client.loop_stop()
        sys.exit()

    #==== MAIN LOOP ====================#
    # MQTT setup successfully. Start Main loop

    try:
        while True:
            clicks, buttonstate = rotEnc1.runencoder()
            if is_integer(clicks):
                outgoingD = {"RotEnc1Ci":str(clicks), "RotEnc1Bi":str(buttonstate)}
                mqtt_client.publish(MQTT_PUB_TOPIC1, json.dumps(outgoingD))
                logging.info("clicks: {0} Button: {1}".format(clicks, buttonstate))
    except KeyboardInterrupt:
        logging.info("Pressed ctrl-C")
    finally:
        rotEnc1.cleanupGPIO()
        logging.info("GPIO cleaned up")