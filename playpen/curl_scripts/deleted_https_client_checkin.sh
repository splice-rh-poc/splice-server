
if [ $# -lt 1 ]; then
    export SAMPLE_RHIC=./sample-deleted.pem
else
    export SAMPLE_RHIC=$1
fi
export SERVER_ADDR=`hostname`
export PORT=443
export CONSUMER_IDENTITY="playpenscript_sample_rhic" # Server doesn't use this value, so putting a dummy value in to identify we are testing for logs
export CA_CERT=/etc/pki/splice/Splice_CA.cert
export DATA="{\"consumer_identifier\":\"F0:DE:F1:DE:88:2B\", \"products\": [\"69\", \"83\", \"183\"], \"system_facts\": {\"tbd\":\"values\"}}"

echo "Using RHIC from ${SAMPLE_RHIC}"
echo curl -s -S -E ${SAMPLE_RHIC} --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X POST --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/entitlement/${CONSUMER_IDENTITY}/ 
curl -s -S -E ${SAMPLE_RHIC} --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X POST --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/entitlement/${CONSUMER_IDENTITY}/ 

