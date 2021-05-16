#!/bin/sh
# usage: aws_service.sh


DATE=`date '+%Y-%m-%d %H:%M:%S'`
echo "AWS IoT service started at ${DATE}" | systemd-cat -p info

/usr/bin/curl http://fred.home:5000/message\?name\=garden-sensor\&message\=AWS%20IoT%20service%20started

cd /home/pi/code/github/SDL_Pi_AM2315


#/usr/bin/python3 awsiot_client.py \
#    --endpoint a2pu44lklh9jkw-ats.iot.eu-west-1.amazonaws.com \
#    --site-name bugsby \
#    --rule-name log_metriful \
#    --topic-root '$aws/rules' \
#    --root-ca /certs/root-CA.crt \
#    --cert /certs/1046d775ec-certificate.pem.crt \
#    --key /certs/1046d775ec-private.pem.key \
#    --sensor-name garden \
#    --debug \
#    | /usr/bin/logger

/usr/bin/python3 awsiot_client.py \
    --debug \
    | /usr/bin/logger
