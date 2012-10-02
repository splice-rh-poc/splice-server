#!/bin/sh
# Script will create a valid certificate
#  valid in the sense cert is signed by shared CA from rhic_serve
# Certificate will be unknown 
#  the subject/CN of the certificate will not be created by rhic_serve
#  therefore it is unknown and may be used to cause a '404' to be returned
#  from the RCS

OUT_DIR="./certs"
CA_KEY="../../etc/pki/splice/Splice_testing_root_CA.key"
CA_CERT="../../etc/pki/splice/Splice_testing_root_CA.crt"
CA_SERIAL="${OUT_DIR}/CA.srl"
RHIC_UUID="1a11111a-11a1-1a11-a11a-11a1a111aa11"
OUTPUT_NAME="unknown_valid_${RHIC_UUID}"
OUT_CERT_NAME="${OUT_DIR}/${OUTPUT_NAME}.cert"
CSR_NAME="${OUT_DIR}/${OUTPUT_NAME}.csr"
KEY_NAME="${OUT_DIR}/${OUTPUT_NAME}.key"

if [ ! -d ${OUT_DIR} ]; then
    mkdir -p ${OUT_DIR}
fi

# Create serial file
if [ ! -f ${CA_SERIAL} ]; then
    echo "01" > ${CA_SERIAL}
fi

openssl genrsa -out ${KEY_NAME} 2048
openssl req -new -key ${KEY_NAME}  -out ${CSR_NAME} -subj "/CN=${RHIC_UUID}"
openssl x509 -req -days 365 -CA ${CA_CERT} -CAkey ${CA_KEY} -in ${CSR_NAME} -out ${OUT_CERT_NAME} -CAserial ${CA_SERIAL}

cat ${OUT_CERT_NAME} >> ${OUT_DIR}/${OUTPUT_NAME}.pem
cat ${KEY_NAME} >> ${OUT_DIR}/${OUTPUT_NAME}.pem


