#!/bin/bash
# Set indigo credentials in environment

# uncomment curl & halt lines to activate

if ! (systemctl -q is-active awsiot-service) then
    logger "[watchdog] awsiot_service is inactive - halting"
    #curl -X EXECUTE -u "$INDIGO_USER:$INDIGO_PASSWORD" --digest http://russ.home:8176/actions/reset-garden-sensor-delayed
    #halt
fi

