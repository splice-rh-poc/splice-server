export SERVER_ADDR=`hostname`
curl -k -s -S --dump-header - -H "Content-Type: application/json" -X GET https://${SERVER_ADDR}/splice/api/v1/rhicrcs/

