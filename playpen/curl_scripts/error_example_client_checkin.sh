export SERVER_ADDR=127.0.0.1
export PORT=8000
export CONSUMER_IDENTITY="tbd_identifier"

curl -s -S -k --dump-header - -H "Content-Type: application/json" -X PUT --data '{"bad_request":""}' http://${SERVER_ADDR}:${PORT}/api/v1/entitlement/${CONSUMER_IDENTITY}/

