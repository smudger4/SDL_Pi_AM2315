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
CONFIG_FILE = './config.json'

# globals
config = {}
log = logging.getLogger("awsiot_service")
simulation = False

def initialise(config_dict, config_file):
    log.info("initialising")
    # load config from file
    with open(config_file) as json_file:
        imported_config = json.load(json_file)
        for key, value in imported_config.items():
            config_dict[key] = value

    log.debug("config: '%s'" % json.dumps(config, indent=4))

    log.info("initialised")


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
                    
    payload['humidity'] = "{:.1f}".format(humidity)
    payload['temperature'] = "{:.1f}".format(temperature)

    # add timestamp
    payload['timestamp'] = str(time.time_ns() // 1_000_000)
    
    log.debug(json.dumps(payload))
    return payload


def main():
    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=config['endpoint'],
        cert_filepath=config['cert'],
        pri_key_filepath=config['key'],
        client_bootstrap=client_bootstrap,
        ca_filepath=config['root-ca'],
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=config['sensor-name'],
        clean_session=False,
        keep_alive_secs=6)

    log.info("Connecting to {} with client ID '{}'...".format(
        config['endpoint'], config['sensor-name']))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    log.info("Connected!")

    # initialise & start sensor
    sensor = AM2315.AM2315()
    topic_name = "{}/{}/{}/{}".format(config['topic-root'], config['site-name'], config['location'], config['sensor-name'])

    while True:
        # read payload from sensor
        payload = read_sensor(sensor)
        payload['location'] = config['location']
        print("Publishing message to topic '{}': {}".format(topic_name, json.dumps(payload)))
        mqtt_connection.publish(
            topic=topic_name,
            payload=json.dumps(payload),
            qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(config['cycle-period'])


if __name__ == "__main__":
    # Create the command line parser
    my_parser = argparse.ArgumentParser(description='Forward AM2315 sensor values to MQTT broker') 

    # Add the arguments
    # mandatory
    my_parser.add_argument('--config-file', default='./config.json', type=str, help='File path to JSON configuration file')

    # optional
    my_parser.add_argument('-d', '--debug', action='store_true', help='Debug level logging')
    my_parser.add_argument('-s', '--simulate', action='store_true', help='Simulation mode (no sensor)')

    # parse command line
    args = my_parser.parse_args()

    # set simulation mode
    simulation = args.simulate

    # set log level
    if (args.debug):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    initialise(config, args.config_file)
    log.info("running")

    main()
