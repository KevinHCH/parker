#!/bin/bash
echo "FLARESOLVER_ENDPOINT=${FLARESOLVER_ENDPOINT}" >> /etc/environment
echo "NOTIFICATION_ENDPOINT=${NOTIFICATION_ENDPOINT}" >> /etc/environment
echo "TZ=${TZ}" >> /etc/environment
# source /etc/environment
. /etc/environment
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

printf "ENVS has been enabled\n"
exec cron -f
