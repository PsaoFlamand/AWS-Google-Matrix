from __future__ import absolute_import
from __future__ import print_function
import argparse
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import signal
import numpy as np
import re

global imp1
global nor1
global H1
global theta


def Giter(nor,H,imp):
    theta=0.85
    a=0
    G=(theta*H)+(1-theta)*nor
    while 1:
        a+=1
        imp0=imp
        imp=imp.dot(G)
        b = np.array([1, 1, 1, 1, 1])
        treaty=imp0[0]-imp[0]
        precisor=[0.000001,0.000001,0.000001,0.000001,0.000001]
        
       # cond0=(treaty[0] < precisor[0]) & (treaty[1] < precisor[1]) & (treaty[2] < precisor[2]) & (treaty[3] < precisor[3]) & (treaty[4] < precisor[4])
        
        if a>50:
            break
    mqtt_connection.publish(
    topic=the_other_topic,
    payload=str(imp),
    qos=mqtt.QoS.AT_LEAST_ONCE)

    print (imp)
    print ("Iterated---> ", a, "times to achieve 10^-6 precision")

def readier(infa):
    N=5
    infa=format(infa.decode("utf-8"))

    #print (np.char.decode(infa))
    n=re.split(",",infa)
    

    H1=np.array([[float(n[0]),float(n[1]),float(n[2]),float(n[3]),float(n[4])], #Construct the H matrix
                 [float(n[5]),float(n[6]),float(n[7]),float(n[8]),float(n[9])],
                 [float(n[10]),float(n[11]),float(n[12]),float(n[13]),float(n[14])],
                 [float(n[15]),float(n[16]),float(n[17]),float(n[18]),float(n[19])],
                 [float(n[20]),float(n[21]),float(n[22]),float(n[23]),float(n[24])]])

    N = H1.shape[1]
    
    imp1=np.array([1/N,1/N,1/N,1/N,1/N]) #construct the importance score matrix

   # print (imp1)
    nor1=np.array([[1/N,1/N,1/N,1/N,1/N], #construct he matrix of 1/N
                  [1/N,1/N,1/N,1/N,1/N],
                  [1/N,1/N,1/N,1/N,1/N],
                  [1/N,1/N,1/N,1/N,1/N],
                  [1/N,1/N,1/N,1/N,1/N]]
                  )
    
    
    print(H1,"/n")
    print(nor1,"/n")
    print(imp1, "/n")
    Giter(nor1,H1,imp1) #Execute the calculation

 

io.init_logging(getattr(io.LogLevel, io.LogLevel.NoLogs.name), 'stderr')

received_count = 0
received_all_event = threading.Event()

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

# MESSAGE RECEIVED
# Callback when the subscribed topic receives a message

def on_message_received(topic, payload, **kwargs):

    readier(payload)


    received_all_event.set()

# Spin up resources
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

#create the MQTT connection

endpoint="a12vgahmsr0jpa-ats.iot.us-east-2.amazonaws.com"
cert_filepath="thing2-cert.pem.crt"
pri_key_filepath="thing2-private-key.pem.key"
ca_filepath="aws-root-cert.pem"
client_id="raspberry-pi"

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=endpoint,
    cert_filepath=cert_filepath,
    pri_key_filepath=pri_key_filepath,
    client_bootstrap=client_bootstrap,
    ca_filepath=ca_filepath,
    on_connection_interrupted=on_connection_interrupted,
    on_connection_resumed=on_connection_resumed,
    client_id=client_id,
    clean_session=False,
    keep_alive_secs=6)

print("Connecting to {} with client ID '{}'...".format(endpoint, client_id))

connect_future = mqtt_connection.connect()

# Waits until a result is available
connect_future.result()
print("Connected!")

my_own_topic = "Thing 2"
the_other_topic = "Thing 1"

#subscribe to topic

print("Listening to '{}' topic...".format(my_own_topic))
subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=my_own_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

subscribe_result = subscribe_future.result()

print("Publishing to '{}' topic...\n".format(the_other_topic))
print("Enter your messages (press Ctrl-C to finish):")

#Infinite loop for sending messages

while(True):
    try:
        msg = input()
#publish message
        mqtt_connection.publish(
            topic=the_other_topic,
            payload=msg,
            qos=mqtt.QoS.AT_LEAST_ONCE)

# Interrupt with Ctrl-C
    except(KeyboardInterrupt,SystemExit):
        break


# Disconnect
print("Disconnecting...")
disconnect_future = mqtt_connection.disconnect()
disconnect_future.result()
print("Disconnected!")
