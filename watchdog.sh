#!/bin/bash
# Set indigo credentials in /etc/environment

# uncomment curl & halt lines to activate

if ! (/usr/bin/systemctl -q is-active awsiot_service) then
    /usr/bin/logger "[watchdog] awsiot_service is inactive - halting"
    #/usr/bin/curl -X EXECUTE -u "$INDIGO_USER:$INDIGO_PASSWORD" --digest http://russ.home:8176/actions/reset-garden-sensor-delayed
    #/usr/sbin/halt
fi
