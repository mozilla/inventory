#!/bin/bash
echo "Building..."
rm -rf ~/dnsbuilds/* &&\
python manage.py bindbuild &&\
sudo rm -rf /etc/invzones/ && \
sudo cp -r ~/dnsbuilds/ /etc/invzones/ &&\
sudo chown -R named /etc/invzones/ &&\
echo "Build complete." &&\
echo "Restarting named..." &&\
sudo /etc/init.d/named restart &&\
echo "Restart Complete."
