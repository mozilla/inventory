#!/bin/bash

MC=$REL_PATH/inventory/mdns/migrate/make_config.py

echo "SYSADMIN_REPO = ''"
echo "$1 = ["

SYSADMINS=$SYSADMINS/sysadmins

for file in $(ls $SYSADMINS/dnsconfig/zones/in-addr/)
do
    if [[ "$file" == "2620-0101" ]]
    then
        continue
    fi
    if [ ! -d $SYSADMINS/dnsconfig/zones/in-addr/$file ]
    then
        continue
    fi
    for file2 in $(ls $SYSADMINS/dnsconfig/zones/in-addr/$file/)
    do
        if [[ "$file2" == "SOA" ]]
        then
            continue
        fi
        if [[ "$file2" == "README" ]]
        then
            continue
        fi
        if [[ "$file2" == "10.14" ]]
        then
            continue
        fi
        if [  -d $SYSADMINS/dnsconfig/zones/in-addr/$file/$file2 ]
        then
            continue
        fi
        python $MC $file2 $SYSADMINS/dnsconfig/zones/in-addr/$file/$file2 r private False
    done

done
echo "]"
