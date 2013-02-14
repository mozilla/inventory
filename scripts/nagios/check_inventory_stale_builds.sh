#!/bin/bash

BIN=/home/juber/inventory_dev/inventory/scripts/dnsbuilds/main.py
PREFIX="[DEV] "

STALE_THRESHOLD=$((60 * 6))  # 6 Min

CRIT=2
WARN=1
OK=0
RET=$OK

eval `$BIN --status`
if [ -f $LAST_RUN_FILE ]
then
    last_run=$(cat $LAST_RUN_FILE)
    now=$(date +%s)
    delta=$((now - last_run))
    mins=$((delta/60))
    if [ $delta -gt $STALE_THRESHOLD ]
    then
        echo -n "$PREFIX"
        echo "CRITICAL: Inventory DNS Builds haven't ran for $mins minutes."
        if [ $STOP_UPDATE_FILE_EXISTS == 'True' ]
        then
            RET=$WARN
        else
            RET=$CRIT
        fi
    else
        echo -n "$PREFIX"
        echo "OK: Inventory DNS Builds have resumed."
    fi
else
    echo -n "$PREFIX"
    echo "WARNING: The LAST_RUN_FILE ("$(hostname)":"$LAST_RUN_FILE") was not found."
    RET=$WARN
fi

exit $RET
