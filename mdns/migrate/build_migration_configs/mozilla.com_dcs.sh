#!/bin/bash

MC=$REL_PATH/inventory/mdns/migrate/make_config.py

echo "SYSADMIN_REPO = ''"
echo "$1 = ["

for file in $(ls $2)
do
    if [ ! -d $2/$file ]
    then
        continue
    fi

    if [ "$file" == "svc" ]
    then
        # Services is weird
        continue
    fi

    python $MC $file.mozilla.com $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/$file/public f public False
    python $MC $file.mozilla.com $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/$file/private f private False

done
    python $MC corp.phx1.mozilla.com $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/phx1/corp/public f public False
    python $MC corp.phx1.mozilla.com $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/phx1/corp/private f private False
echo "]"
