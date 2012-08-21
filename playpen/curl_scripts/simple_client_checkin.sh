export SERVER_ADDR=127.0.0.1
export PORT=8000
export CONSUMER_IDENTITY="tbd_identifier"

#curl -s -S -k -H "Content-Type: application/json" -X PUT --data '{"identity_cert":"TEXT_WOULD_GO_HERE", "products": ["PRODUCT1", "PRODUCT2"]}' http://${SERVER_ADDR}:${PORT}/api/v1/entitlement/${CONSUMER_IDENTITY}/ | python -mjson.tool
curl -s -S -k --dump-header - -H "Content-Type: application/json" -X PUT --data '{"identity_cert":"TEXT_WOULD_GO_HERE", "consumer_identifier":"F0:DE:F1:DE:88:2B", "products": ["PRODUCT1", "PRODUCT2"]}' http://${SERVER_ADDR}:${PORT}/splice/api/v1/entitlement/${CONSUMER_IDENTITY}/ 
