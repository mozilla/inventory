#!/bin/bash
rm -rf ~/dnsbuilds/*
python manage.py bindbuild
sudo rm -rf /etc/invzones/
sudo cp -r ~/dnsbuilds/ /etc/invzones/
sudo chown -R named /etc/invzones/
