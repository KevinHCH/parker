#!/bin/bash
echo "FLARESOLVER_ENDPOINT=${FLARESOLVER_ENDPOINT}" >> /etc/environment
echo "NOTIFICATION_ENDPOINT=${NOTIFICATION_ENDPOINT}" >> /etc/environment
# source /etc/environment
. /etc/environment 

printf "ENVS has been enabled\n"
exec cron -f
