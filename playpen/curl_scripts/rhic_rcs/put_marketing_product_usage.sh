source source_me
export SERVER_ADDR=`hostname`
curl -v --cacert ${CA_CERT} --cert ${CLIENT_CERT} --key ${CLIENT_KEY}  --data @mkt.json -s -S  -H "Content-Type: application/json" -X POST https://${SERVER_ADDR}:443/splice/api/v1/marketingproductusage/
