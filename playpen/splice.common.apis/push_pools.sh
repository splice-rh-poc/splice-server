#!/bin/sh

export SERVER_ADDR=`hostname`
export PORT=443
export CA_CERT=/etc/pki/splice/generated/Splice_HTTPS_CA.cert
export CLIENT_CERT=/etc/pki/consumer/Splice_identity.cert
export CLIENT_KEY=/etc/pki/consumer/Splice_identity.key
export SAMPLE_JSON=./pools.json

#curl -s -S --cacert ${CA_CERT} --cert ${CLIENT_CERT} --key ${CLIENT_KEY} --dump-header - -H "Content-Type: application/json" -X POST --data @${SAMPLE_JSON} https://${SERVER_ADDR}:${PORT}/splice/api/v1/pool/  --trace-ascii curl_log
curl -s -S -k --cert ${CLIENT_CERT} --key ${CLIENT_KEY} --dump-header - -H "Content-Type: application/json" -X POST --data @${SAMPLE_JSON} https://${SERVER_ADDR}:${PORT}/splice/api/v1/pool/  --trace-ascii curl_log

