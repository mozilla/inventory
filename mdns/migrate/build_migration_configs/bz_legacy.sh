#!/bin/bash
MC=$REL_PATH/inventory/mdns/migrate/make_config.py

echo "SYSADMIN_REPO = ''"
echo "$1 = ["

for file in $(ls $2)
do
    if [[ $file == *.signed ]]
    then
        continue
    fi

    if [[ $file == *-start ]]
    then
        # mozilla.com-start
        continue
    fi

    if [[ $file == *-common ]]
    then
        # mozilla.com-common
        # mozilla.org-common
        # mozilla.office-common
        # 
        continue
    fi

    if [[ $file == *-update ]]
    then
        # mozilla.org-update
        continue
    fi

    if [[ $file == *-cnames ]]
    then
        # mozilla.org-cnames
        continue
    fi
    if [[ $file == *-ftp ]]
    then
        # mozilla.org-ftp
        continue
    fi
    if [[ $file == *-mpt ]]
    then
        # mozilla.org-mpt
        continue
    fi
    if [[ $file == *-office ]]
    then
        # mozilla.org-office
        continue
    fi
    if [[ $file == *-office-common ]]
    then
        # mozilla.org-office-common
        continue
    fi
    if [[ $file == *-office-external ]]
    then
        # mozilla.org-office-external
        continue
    fi
    if [[ $file == *-osuosl ]]
    then
        # mozilla.org-osuosl
        continue
    fi
    if [[ $file == *-soa ]]
    then
        # mozilla.org-soa
        continue
    fi
    if [[ $file == *-update ]]
    then
        # mozilla.org-update
        continue
    fi
    if [[ $file == *-www ]]
    then
        # mozilla.org-www
        continue
    fi

    if [[ $file == *-osuosl ]]
    then
        # mozilla.org-www
        continue
    fi

    if [[ "$file" == "cn.mozilla.com" ]]
    then
        continue
    fi

    if [[ "$file" == "ca.mozilla.com" ]]
    then
        continue
    fi

    if [[ $file == db.140.211* ]]
    then
        continue
    fi

    if [[ $file == db.207.126.111.192 ]]
    then
        continue
    fi

    if [[ $file == dk.mozilla.com ]]
    then
        continue
    fi

    if [[ $file == mv.mozilla.com ]]
    then
        # Included in -common
        continue
    fi

    if [[ $file == nl.mozilla.com ]]
    then
        # Included in -common
        continue
    fi

    if [[ $file == sj.mozilla.com ]]
    then
        continue
    fi

    if [[ $file == "nl.mozilla.com-213" ]]
    then
        continue
    fi

    if [[ $file == db.* ]]
    then
        zone_name=$(echo "$file" | sed -s 's/db.//')
        python $MC $zone_name $REL_PATH/sysadmins/dnsconfig/external/$file r both False
    elif [[ $file == *.in-addr.arpa ]]
    then
        zone_name=$(echo "$file" | sed -s 's/.in-addr.arpa//')
        python $MC $zone_name $REL_PATH/sysadmins/dnsconfig/external/$file r both True
    else
        python $MC $file $REL_PATH/sysadmins/dnsconfig/external/$file f both False
    fi
done
echo "]"
