#!/bin/sh

if [ $# -lt 2 ]; then
    echo "Usage: $0 REMOTE_HOSTNAME PATH_TO/sample-certgen-products.json"
    exit 1
fi
export HOSTNAME=$1
export CERTMAKER_DATA=$2

# Upload product data to cert-maker
echo "Uploading product data from ${CERTMAKER_DATA} to splice-certmaker on ${HOSTNAME}"
echo "curl -X POST --data \"product_list=\`cat ${CERTMAKER_DATA}\`\"  http://${HOSTNAME}:8080/productlist"
curl -X POST --data "product_list=`cat ${CERTMAKER_DATA}`"  http://${HOSTNAME}:8080/productlist
