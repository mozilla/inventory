#!/bin/bash

BIN=""
PREFIX="[DEV] "

CRIT=2
WARN=1
OK=0
RET=$OK

eval $($BIN --status)
if [ $STOP_UPDATE_FILE_EXISTS == 'True' ]
then
    echo -n "$PREFIX"
    echo "CRITICAL: Inventory DNS Builds have stopped. Stop update file at" $(hostname)":"$STOP_UPDATE_FILE
    RET=$CRIT
else
    echo -n "$PREFIX"
    echo "OK: Inventory DNS Builds will resume. Stop update file has been removed"
fi

exit 0
