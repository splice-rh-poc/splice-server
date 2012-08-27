export SERVER_ADDR=`hostname`
export PORT=443
export SAMPLE_RHIC=../../src/splice/test_data/valid_cert/sample_rhic_valid.pem
export CA_CERT=/etc/pki/splice/Splice_CA.cert
export CONSUMER_IDENTITY="dbcbc8e1-5b37-4a77-9db1-faf4ef29307d"
export DATA="{\"consumer_identifier\":\"F0:DE:F1:DE:88:2B\", \"products\": [\"37060\", \"37062\"]}"

echo curl -s -S -E ${SAMPLE_RHIC} --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X PUT --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/entitlement/${CONSUMER_IDENTITY}/ 
curl -s -S -E ${SAMPLE_RHIC} --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X PUT --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/entitlement/${CONSUMER_IDENTITY}/ 

