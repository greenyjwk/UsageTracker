import serial
import time
import requests
import serial,sys,glob
import serial.tools.list_ports as COMs
import asyncio
from awscrt import mqtt
import threading
from uuid import uuid4
import json

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.


# This sample uses the Message Broker for AWS IoT to send and receive messages
# through an MQTT connection. On startup, the device connects to the server,
# subscribes to a topic, and begins publishing messages to that topic.
# The device should receive those same messages back from the message broker,
# since it is subscribed to that same topic.


def send_command(ser, command):
    ser.write(command.encode())


def check_ack(ser, ack_string): 
    i = 0 
    storage = [None] * 2
    while i < 2:
        recd_ack = ser.readline().decode('utf-8')   # Read and print the received serial transmission
        # print(recd_ack)
        splitted = recd_ack.split()
        outcome = splitted[0]
        print(i)
        print(outcome)
        storage[i] = outcome
        i = i+1
        if (recd_ack == ack_string + "\r\n"):   # Check if the recieved message is an acknowledgement message
            # print(ack_string + " received")
            break
    print(storage)
    
    
    # i = 0
    # temperature = 0
    # light = 1
    
    # recd_ack = ser.readline().decode('utf-8')   # Read and print the received serial transmission
    # # while i < 2:
    # print("------")
    # print(recd_ack)
    # splitted = recd_ack.split()
    # outcome = splitted[0]
    # # print(outcome)
    # print(i)
    # print("------")

    # if i/2 == 0:
    #     temperature = outcome
    # else:
    #     light = outcome
    # i = i+1
    
    # # if (recd_ack == ack_string + "\r\n"):   # Check if the recieved message is an acknowledgement message
    #     # break
    
    return storage


def port_search():
    if sys.platform.startswith('win'): # Windows
        ports = ['COM{0:1.0f}'.format(ii) for ii in range(1,256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'): # MAC
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Machine Not pyserial Compatible')

    arduinos = []
    for port in ports: # loop through to determine if accessible
        if len(port.split('Bluetooth'))>1:
            continue
        try:
            ser = serial.Serial(port)
            ser.close()
            arduinos.append(port) # if we can open it, consider it an arduino
        except (OSError, serial.SerialException):
            pass
    return arduinos



def get_volcano_data():

###########

    url = 'https://api.weather.gov/stations/KROC/observations/latest'

    response = requests.get(url)
    data = response.json()
    temperature = data['properties']['temperature']['value']
    dewpoint = data['properties']['dewpoint']['value']
    wind_speed = data['properties']['windSpeed']['value']
    wind_direction = data['properties']['windDirection']['value']
    timestamp = data['properties']['timestamp']
    id = data['properties']["@id"]
    HI = data['properties']["heatIndex"]['value']
    windChill = data['properties']["windChill"]['value']

    angle = 0
    severityLevel = 0

    if HI == None:
        
        intwindChill = int(windChill)
        if intwindChill > -25 :
            severityLevel = "Cold"
            angle = 101
        elif intwindChill > -35 & intwindChill < -25:
            severityLevel = "Very Cold"
            angle = 124
        elif intwindChill > -60 & intwindChill < -35:
            severityLevel = "Danger"
            angle = 146
        elif intwindChill < -60:
            severityLevel = "Great Danger"
            angle = 169
        # print('Severity:', severityLevel)
        # print('Servo Angle: ', angle)
        return windChill

    elif windChill == None:
        
        intHI = int(HI)
        if intHI > 26 & intHI < 32 :
            severityLevel = "Caution"
            angle = 79
        elif intHI > 32 & intHI < 41:
            severityLevel = "Extreme Caution"
            angle = 56
        elif intHI > 41 & intHI < 54:
            severityLevel = "Danger"
            angle = 34
        elif intHI < 54:
            severityLevel = "Extreme Danger"
            angle = 11
        # print('Severity: ', severityLevel)
        # print('Servo Angle: ', angle)
        return HI
    else:
        print("Normal")
        severityLevel ="Normal"
        return None



# def main():
    # arduino_ports = port_search()
    # print(arduino_ports)
    # ser = serial.Serial(arduino_ports[0],baudrate=9600) # match baud on Arduino
    # ser.flush() # waiting until the transmission is complete
    
    # # data = get_volcano_data()
    # send_command(ser, "COM_VOLCANO_LEVEL")
    # check_ack(ser, "ACK_VOLCANO_LEVEL")    
    # send_command(ser, str(data))
    # check_ack(ser, "ACK_VOLCANO_LEVEL")



# Parse arguments
import command_line_utils as command_line_utils
cmdUtils = command_line_utils.CommandLineUtils("PubSub - Send and recieve messages through an MQTT connection.")
cmdUtils.add_common_mqtt_commands()
cmdUtils.add_common_topic_message_commands()
cmdUtils.add_common_proxy_commands()
cmdUtils.add_common_logging_commands()
cmdUtils.register_command("key", "<path>", "Path to your key in PEM format.", True, str)
cmdUtils.register_command("cert", "<path>", "Path to your client certificate in PEM format.", True, str)
cmdUtils.register_command("port", "<int>", "Connection port. AWS IoT supports 443 and 8883 (optional, default=auto).", type=int)
cmdUtils.register_command("client_id", "<str>", "Client ID to use for MQTT connection (optional, default='test-*').", default="test-" + str(uuid4()))
cmdUtils.register_command("count", "<int>", "The number of messages to send (optional, default='10').", default=10, type=int)
cmdUtils.register_command("is_ci", "<str>", "If present the sample will run in CI mode (optional, default='None')")
# Needs to be called so the command utils parse the commands
cmdUtils.get_args()








received_count = 0
received_all_event = threading.Event()
is_ci = cmdUtils.get_command("is_ci", None) != None

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    # print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == cmdUtils.get_command("count"):
        received_all_event.set()



def temp():
    arduino_ports = port_search()
    print(arduino_ports)
    ser = serial.Serial(arduino_ports[0],baudrate=9600) # match baud on Arduino
    ser.flush() # waiting until the transmission is complete
    data = get_volcano_data()
    send_command(ser, "COM_VOLCANO_LEVEL")
    check_ack(ser, "ACK_VOLCANO_LEVEL")
    send_command(ser, str(data))
    check_ack(ser, "ACK_VOLCANO_LEVEL")


if __name__ == "__main__":
    # temp()

    mqtt_connection = cmdUtils.build_mqtt_connection(on_connection_interrupted, on_connection_resumed)
    
    
    arduino_ports = port_search()
    print(arduino_ports)
    ser = serial.Serial(arduino_ports[0],baudrate=9600) # match baud on Arduino
    ser.flush() # waiting until the transmission is complete
    data = get_volcano_data()
    
    temperature = 0
    light = 1


    if is_ci == False:
        print("Connecting to {} with client ID '{}'...".format(
            cmdUtils.get_command(cmdUtils.m_cmd_endpoint), cmdUtils.get_command("client_id")))
    else:
        print("Connecting to endpoint with client ID")
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    message_count = cmdUtils.get_command("count")
    message_topic = cmdUtils.get_command(cmdUtils.m_cmd_topic)

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,     # AT_LEAST_ONCE is equivalent to QOS 1, if you want to use QOS 0, change it to AT_MOST_ONCE
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))


    message_string = "testing_connection"              #Input your own message in this feild to publish to AWS.
    

    ts = time.time()

    # Publish message to server desired number of times.
    # This step is skipped if message is blank.
    # This step loops forever if count was set to 0.
    if message_string:
        if message_count == 0:
            print ("Sending messages until program killed")
        else:
            print ("Sending {} message(s)".format(message_count))

        publish_count = 1
        while (publish_count <= message_count) or (message_count == 0):

            send_command(ser, "COM_VOLCANO_LEVEL")
            storageReturn = check_ack(ser, "ACK_VOLCANO_LEVEL")
            message_string = { "Temperature": storageReturn[0], "Light": storageReturn[1] }
            

            message_string = { "timestamp": ts,
                              "MAC": "1c:57:dc:26:f5:25",
                              "sensorData":[
                                    {
                                        "Temperature": storageReturn[0], 
                                        "Light": storageReturn[1]
                                    }
                                ]                
                              }


            message = "{} [{}]".format(message_string, publish_count)
            # print("Publishing message to topic '{}': {}".format(message_topic, message))
            print("Publishing message to topic '{}': {}".format(storageReturn[0], storageReturn[1]))
            message_json = json.dumps(message)
            mqtt_connection.publish(
                topic=message_topic,
                payload=message_json,
                qos=mqtt.QoS.AT_LEAST_ONCE)     # AT_LEAST_ONCE is equivalent to QOS 1, if you want to use QOS 0, change it to AT_MOST_ONCE
            # time.sleep(5)
            publish_count += 1

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if message_count != 0 and not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")




