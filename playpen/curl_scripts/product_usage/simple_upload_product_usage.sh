#!/bin/sh

export SERVER_ADDR=`hostname`
export PORT=443
export CA_CERT=/etc/pki/splice/generated/Splice_CA.cert
export DATA="[{
\"consumer\":\"fb647f68-aa01-4171-b62b-35c2984a5328\", 
\"instance_identifier\":\"F0:DE:F1:DE:88:2B\", 
\"allowed_product_info\": [\"69\", \"83\", \"183\"], 
\"unallowed_product_info\": [\"0\"], 
\"facts\": {\"tbd\":\"values\"},
\"date\": \"2012-10-17 18:05:11.839000\",
\"splice_server\": \"aa111a11-aa01-1111-a00a-00a1111a1111\"
}]"

echo curl -s -S --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X POST --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/productusage/ 
curl -s -S --cacert ${CA_CERT} --dump-header - -H "Content-Type: application/json" -X POST --data "${DATA}" https://${SERVER_ADDR}:${PORT}/splice/api/v1/productusage/ 


