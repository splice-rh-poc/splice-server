#!/bin/sh
source ./config

for i in {1..1000}
do
    KEY_NAME=${KEY_PREFIX}_${i}.key
    CSR_NAME=${CSR_PREFIX}_${i}.csr
    OUT_CERT_NAME=${OUT_CERT_PREFIX}_${i}.cert
    openssl genrsa -out ${KEY_NAME} 2048
    openssl req -new -key ${KEY_NAME}  -out ${CSR_NAME} -subj '/C=US/ST=NC/L=Raleigh/O=Red Hat/OU=Splice/CN=test' 
    openssl x509 -req -days 365 -CA ${CA_CERT} -CAkey ${CA_KEY} -extfile ${EXTENSION_FILE} -extensions pulp-repos -in ${CSR_NAME} -out ${OUT_CERT_NAME} -CAserial ${CA_SERIAL}

done


