#!/bin/bash
# watchdog script to check to see if the sensor service has died
# if so, likely that sensor needs a power-cycle to recover
# ask home automation to power-cycle the system
# home automation command has a delay built in to allow time for a clean shutdown

# Set Indigo credentials in /etc/environment
# copy to /usr/local/bin as root before adding to root crontab
# active lines commented out for safety - uncomment in version run by crontab

if ! (/usr/bin/systemctl -q is-active awsiot_service) then
    /usr/bin/logger "[watchdog] awsiot_service is inactive - halting"
    #/usr/bin/curl -X EXECUTE -u "$INDIGO_USER:$INDIGO_PASSWORD" --digest $INDIGO_URL
    #/usr/sbin/halt
fi
