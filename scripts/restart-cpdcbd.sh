#!/bin/sh

sudo sv restart csfrd
sudo sv restart csfrd-testnet
sleep 10
sudo sv restart csfrblockd
sudo sv restart csfrblockd-testnet
