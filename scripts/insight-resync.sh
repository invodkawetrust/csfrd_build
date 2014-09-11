#!/bin/sh
CURDIR=`pwd`
cd /home/sfr/insight-api
export BITCOIND_DATADIR=/home/sfr/.saffroncoin/
export BITCOIND_USER=`cat /home/sfr/.saffroncoin/saffroncoin.conf | sed -n 's/.*rpcuser=\([^ \n]*\).*/\1/p'`
export BITCOIND_PASS=`cat /home/sfr/.saffroncoin/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'`
INSIGHT_NETWORK=livenet INSIGHT_DB=/home/sfr/insight-api/db util/sync.js -D
cd $CURDIR
