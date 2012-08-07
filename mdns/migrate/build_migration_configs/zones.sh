#!/bin/bash
MC=$REL_PATH/inventory/mdns/migrate/make_config.py

echo "SYSADMIN_REPO = ''"
echo "$1 = ["

for file in $(ls $2)
do
    if [ -d $2/$file ]
    then
        continue
    fi
    python $MC $file $REL_PATH/sysadmins/dnsconfig/zones/$file f public False
done
echo "]"
