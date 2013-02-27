if [ $# -lt 2 ]; then
    echo "Usage: $0 CANDLEPIN_HOST CANDLEPIN_PORT"
    exit 1
fi
export HOST=$1
export PORT=$2

curl -k -u admin:admin -D ./rules.header https://$1:$2/candlepin/rules &> rules.data



