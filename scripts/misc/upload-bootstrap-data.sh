#!/bin/sh
#Sample script to get and upload csfrd bootstrap data to s3
# Requires s3cmd (sudo apt-get install s3cmd; sudo s3cmd --configure)
#This script could then be configured and put into your /etc/cron.daily dir for instance

export CPD_USER_NAME=local
export CPD_USER_HOMEDIR=$(eval echo ~${CPD_USER_NAME})
S3_CONTAINER_NAME="csfr-bootstrap"

echo "Stopping services..."
service csfrd stop
service csfrd-testnet stop

echo "Creating tarball (mainnet)..."
rm -f /tmp/csfrd-db.latest.tar.gz /tmp/csfrd-testnet-db.latest.tar.gz
cd ${CPD_USER_HOMEDIR}/.config/csfrd/ && tar -czvf /tmp/csfrd-db.latest.tar.gz csfrd.9.db*
s3cmd --force --bucket-location=US -P put /tmp/csfrd-db.latest.tar.gz s3://${S3_CONTAINER_NAME}/
rm -f /tmp/csfrd-db.latest.tar.gz

echo "Creating tarball (testnet)..."
cd ${CPD_USER_HOMEDIR}/.config/csfrd-testnet/ && tar -czvf /tmp/csfrd-testnet-db.latest.tar.gz csfrd.9.testnet.db*
s3cmd --force --bucket-location=US -P put /tmp/csfrd-testnet-db.latest.tar.gz s3://${S3_CONTAINER_NAME}/
rm -f /tmp/csfrd-testnet-db.latest.tar.gz

echo "Updating csfrd from git..."
/bin/bash -c 'cd ${CPD_USER_HOMEDIR}/csfrd_build && SUDO_USER=${CPD_USER_NAME} ./setup.py update'

echo "Restarting services..."
service csfrd start
service csfrd-testnet start
