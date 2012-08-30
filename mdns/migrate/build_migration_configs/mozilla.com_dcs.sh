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
    if [ "$file" == "services" ]
    then
        #mozilla.com/services/public:10:$GENERATE 1-100 stage-sync$     IN  CNAME   stage-sync
        #mozilla.com/services/public:25:$GENERATE 1-40 phx-sync${0,2,d} IN  CNAME   sync-rr.phx.services.mozilla.com.
        #mozilla.com/services/public:26:$GENERATE 0-609 phx-sync${0,3,d} IN CNAME sync-rr.phx.services.mozilla.com.
        #mozilla.com/services/public:37:$GENERATE 1-1320 scl2-sync$     IN  CNAME   scl2-sync
        #mozilla.com/services/public:56:$GENERATE 1-230 beta-sync$      IN  CNAME   beta-sync
        #mozilla.com/services/private:6:$GENERATE 1-40 stage-sync${0,2,d} IN CNAME    stage-sync
        #mozilla.com/services/private:13:$GENERATE 1-40 dev-sync${0,2,d} IN CNAME    dev-sync
        # So many records that it crashes the import script. Going to have to do this directory by hand.
        continue
    fi

    python $MC $file.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/$file/public f both False
    python $MC $file.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/$file/private f private False
    if [ -f $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/$file/public.split ]
    then
        python $MC $file.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/$file/public.split f public False
    fi
    if [ -f $REL_PATH/sysadmins/dnsconfig/zones/mozilla.com/$file/private.split ]
    then
        python $MC $file.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/$file/private.split f private False
    fi

done
    python $MC corp.phx1.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/phx1/corp/public f both False
    python $MC corp.phx1.mozilla.com $SYSADMINS/sysadmins/dnsconfig/zones/mozilla.com/phx1/corp/private f private False

echo "]"
