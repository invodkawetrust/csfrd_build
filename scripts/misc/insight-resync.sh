#!/bin/sh
CURDIR=`pwd`
cd /home/csfr/insight-api
export BITCOIND_DATADIR=/home/csfr/.saffroncoin/
export BITCOIND_USER=`cat /home/csfr/.saffroncoin/saffroncoin.conf | sed -n 's/.*rpcuser=\([^ \n]*\).*/\1/p'`
export BITCOIND_PASS=`cat /home/csfr/.saffroncoin/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'`
INSIGHT_NETWORK=livenet INSIGHT_DB=/home/csfr/insight-api/db util/sync.js -D
cd $CURDIR
