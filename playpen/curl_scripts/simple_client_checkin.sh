export SERVER_ADDR=127.0.0.1
export PORT=8000
#
# Need to fix server side error of 'Invalid control character ', I think this
# is caused by embedded newline breaks in the cert.
#
export IDENTITY_CERT=`cat ../../src/splice/test_data/valid_cert/valid.cert`
export CONSUMER_IDENTITY="dbcbc8e1-5b37-4a77-9db1-faf4ef29307d"
export DATA="{\"identity_cert\":\"${IDENTITY_CERT}\", \"consumer_identifier\":\"F0:DE:F1:DE:88:2B\", \"products\": [\"PRODUCT1\", \"PRODUCT2\"]}"
echo "DATA:  ${DATA}"
curl -s -S -k --dump-header - -H "Content-Type: application/json" -X PUT --data "${DATA}" http://${SERVER_ADDR}:${PORT}/api/v1/entitlement/${CONSUMER_IDENTITY}/ 
