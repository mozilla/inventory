#!/bin/bash
#ams
#cn (kind of zone)
# X external
#mozilla.com
#  ad
#  akl1
#  ams1
#  any1
#  lon1
#  mtv1
#  pao1
#  par1
#  par2
#  pek1
#  pek2
#  phx1
#  scl1
#  scl2
#  scl3
#  services
#  sfo1
#  sjc1
#  sjc2
#  SOA
#  svc
#  tor1
#  tpe1
#  weave
#  yvr1

#mozilla.net
#mozilla.org
#mpt-dmz
#named.ca
#named.local
#named.stats
#offices
#phx
#slave-config
#slaves
#templates
#weave
#zeusglb
#zones

BZ=$HOME/inventory/mdns/migrate/build_migration_configs/bz_legacy.sh
ZONE_CONFIGS=$HOME/inventory/mdns/migrate/zone_configs
rm -rf $ZONE_CONFIGS
mkdir $ZONE_CONFIGS
touch $ZONE_CONFIGS/__init__.py

#$BZ cn $HOME/sysadmins/dnsconfig/cn > $ZONE_CONFIGS/cn_zone_config.py
#python $ZONE_CONFIGS/cn_zone_config.py

#$BZ external $HOME/sysadmins/dnsconfig/external > $ZONE_CONFIGS/external_zone_config.py
#python $ZONE_CONFIGS/external_zone_config.py

$BZ phx $HOME/sysadmins/dnsconfig/phx > $ZONE_CONFIGS/phx_zone_config.py
python $ZONE_CONFIGS/phx_zone_config.py

./build_migration_configs/mozilla.com_dcs.sh mozilla_com_dcs ~/sysadmins/dnsconfig/mozilla.com > $ZONE_CONFIGS/mozilla_com_dc_zone_config.py
python $ZONE_CONFIGS/mozilla_com_dc_zone_config.py

./build_migration_configs/zones_reverse.sh private_reverse ~/sysadmins/dnsconfig/mozilla.com > $ZONE_CONFIGS/private_reverse.py
python $ZONE_CONFIGS/private_reverse.py

./build_migration_configs/bz_legacy.sh external $HOME/sysadmins/dnsconfig/external > $ZONE_CONFIGS/external.py
python $ZONE_CONFIGS/external.py

