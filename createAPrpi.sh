#!/bin/bash
APNAME="Rover"
APPASS="roverontop"
nmcli con add type wifi ifname wlan0 con-name $APNAME autoconnect yes ssid $APNAME
nmcli con modify $APNAME 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
nmcli con modify $APNAME wifi-sec.key-mgmt wpa-psk
nmcli con modify $APNAME wifi-sec.psk "$APPASS"
nmcli con up $APNAME