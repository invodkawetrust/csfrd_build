#!/bin/sh
CURDIR=`pwd`
cd ~csfr/insight-api
export BITCOIND_DATADIR=/home/csfr/.saffroncoin-testnet/
export BITCOIND_USER=`cat /home/csfr/.saffroncoin-testnet/saffroncoin.conf | sed -n 's/.*rpcuser=\([^ \n]*\).*/\1/p'`
export BITCOIND_PASS=`cat /home/csfr/.saffroncoin-testnet/saffroncoin.conf | sed -n 's/.*rpcpassword=\([^ \n]*\).*/\1/p'`
INSIGHT_NETWORK=testnet INSIGHT_DB=/home/csfr/insight-api/db util/sync.js -D
cd $CURDIR
