import time
import logging
import json
import argparse
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import sys
import threading
import AM2315
from uuid import uuid4

# defaults
DEFAULT_CYCLE_PERIOD = 5
DEFAULT_TOPIC_ROOT = "$aws/rules"

# globals
log = logging.getLogger("mqtt_publisher")
simulation = False

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
def on_message_received(topic, payload, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == args.count:
        received_all_event.set()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    log.info("Connected to broker with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    log.info(msg.topic+" "+str(msg.payload))

def read_sensor(sensor):
    # read temp & humidity from sensor & add to payload dict
    payload = {}
    humidity, temperature = sensor.read_humidity_temperature()
                    
    payload['humidity'] = "{:.2f}".format(humidity)
    payload['temperature'] = "{:.2f}".format(temperature)

    # add timestamp
    payload['timestamp'] = str(time.time_ns() // 1_000_000)
    
    log.debug(json.dumps(payload))
    return payload


def main(sensor_name, endpoint, site_name, rule_name, topic_root, cert, root_ca, key, cycle_period, debug_flag):
    if (debug_flag):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert,
        pri_key_filepath=key,
        client_bootstrap=client_bootstrap,
        ca_filepath=root_ca,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=sensor_name,
        clean_session=False,
        keep_alive_secs=6)

    print("Connecting to {} with client ID '{}'...".format(
        endpoint, sensor_name))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    # initialise & start sensor
    sensor = AM2315.AM2315()
    topic_name = "{}/{}/{}/{}".format(topic_root, rule_name, site_name, sensor_name)
    while True:
        # read payload from sensor
        payload = read_sensor(sensor)
        payload['location'] = sensor_name
        print("Publishing message to topic '{}': {}".format(topic_name, json.dumps(payload)))
        mqtt_connection.publish(
            topic=topic_name,
            payload=json.dumps(payload),
            qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(cycle_period)


if __name__ == "__main__":
    # Create the command line parser
    my_parser = argparse.ArgumentParser(description='Forward AM2315 sensor values to MQTT broker') 

    # Add the arguments
    # mandatory
    my_parser.add_argument('--sensor-name', required=True, type=str, help='Name of this sensor')
    my_parser.add_argument('--endpoint', required=True, help="Your AWS IoT custom endpoint, not including a port. " +
                                                      "Ex: \"abcd123456wxyz-ats.iot.us-east-1.amazonaws.com\"")
    my_parser.add_argument('--site-name', required=True, help="Site name for AWS IoT connection.")
    my_parser.add_argument('--rule-name', required=True, help="IoT Rule name for AWS IoT connection.")

    my_parser.add_argument('--cert', required=True, help="File path to your client certificate, in PEM format.")
    my_parser.add_argument('--key', required=True, help="File path to your private key, in PEM format.")
    my_parser.add_argument('--root-ca', required=True, help="File path to root certificate authority, in PEM format. " +
                                        "Necessary if MQTT server uses a certificate that's not already in " +
                                        "your trust store.")

    # optional
    my_parser.add_argument('--topic-root', default=DEFAULT_TOPIC_ROOT, help="MQTT Topic root for AWS IoT connection.")
    my_parser.add_argument('--cycle_period', default=DEFAULT_CYCLE_PERIOD, help="How frequently to read sensor, in seconds.")
    my_parser.add_argument('-d', '--debug', action='store_true', help='Debug level logging')

    # parse command line
    args = my_parser.parse_args()

    # check if cycle period provided parses to an int
    try:
        cycle_period = int(args.cycle_period)
    except TypeError:
        log.error("cycle-period argument must be an integer - defaulting to %s seconds" % DEFAULT_CYCLE_PERIOD)
        cycle_period = DEFAULT_CYCLE_PERIOD

    main(args.sensor_name, args.endpoint, args.site_name, args.rule_name, args.topic_root, args.cert, args.root_ca, args.key, cycle_period, args.debug)
