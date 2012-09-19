export SERVER_ADDR=127.0.0.1
export CONSUMER_IDENTITY="tbd_identifier"

curl -s -S -k --dump-header - -H "Content-Type: application/json" -X POST --data '{"bad_request":""}' https://${SERVER_ADDR}/api/v1/entitlement/${CONSUMER_IDENTITY}/

