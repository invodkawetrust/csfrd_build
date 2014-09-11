#!/bin/sh
CURDIR=`pwd`
cd ~sfr/insight-api
export BITCOIND_DATADIR=/home/sfr/.saffroncoin-testnet/
export BITCOIND_USER=`cat /home/sfr/.saffroncoin-testnet/saffroncoin.conf | sed -n 's/.*rpcuser=\([^ \n]*\).*/\1/p'`
export BITCOIND_PASS=`cat /home/sfr/.saffroncoin-testnet/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'`
INSIGHT_NETWORK=testnet INSIGHT_DB=/home/sfr/insight-api/db util/sync.js -D
cd $CURDIR
