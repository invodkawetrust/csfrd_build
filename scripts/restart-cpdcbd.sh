#!/bin/sh

sudo service csfrd restart
sudo service csfrd-testnet restart
sleep 10
sudo service csfrblockd restart
sudo service csfrblockd-testnet restart
