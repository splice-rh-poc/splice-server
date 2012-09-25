#!/bin/sh
source ./config


if [ ! -d ${OUT_DIR} ]; then
    mkdir -p ${OUT_DIR}
fi

# Create the CA key & cert
openssl genrsa -out ${CA_KEY} 2048
openssl req -new -x509 -days 10950 -key ${CA_KEY} -out ${CA_CERT} -subj '/C=US/ST=NC/L=Raleigh/O=Red Hat/OU=Splice/CN=Splice-Root-CA'
# Create serial file
echo "01" > ${CA_SERIAL}

# Generate an extensions file
echo "
[pulp-repos]
basicConstraints=CA:FALSE
1.3.6.1.4.1.2312.9.2.0000.1.1=ASN1:UTF8:Pulp Production Fedora 15
1.3.6.1.4.1.2312.9.2.0000.1.2=ASN1:UTF8:pulp-prod-f15
1.3.6.1.4.1.2312.9.2.0000.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-15/i386/

1.3.6.1.4.1.2312.9.2.0001.1.1=ASN1:UTF8:Pulp Production Fedora 15
1.3.6.1.4.1.2312.9.2.0001.1.2=ASN1:UTF8:pulp-prod-f15
1.3.6.1.4.1.2312.9.2.0001.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-15/x86_64/

1.3.6.1.4.1.2312.9.2.0002.1.1=ASN1:UTF8:Pulp Production Fedora 14
1.3.6.1.4.1.2312.9.2.0002.1.2=ASN1:UTF8:pulp-prod-f14
1.3.6.1.4.1.2312.9.2.0002.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-14/i386/

1.3.6.1.4.1.2312.9.2.0003.1.1=ASN1:UTF8:Pulp Production Fedora 14
1.3.6.1.4.1.2312.9.2.0003.1.2=ASN1:UTF8:pulp-prod-f14
1.3.6.1.4.1.2312.9.2.0003.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-14/x86_64/

1.3.6.1.4.1.2312.9.2.0004.1.1=ASN1:UTF8:Pulp Production Fedora 16
1.3.6.1.4.1.2312.9.2.0004.1.2=ASN1:UTF8:pulp-prod-f16
1.3.6.1.4.1.2312.9.2.0004.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-16/i386/

1.3.6.1.4.1.2312.9.2.0005.1.1=ASN1:UTF8:Pulp Production Fedora 16
1.3.6.1.4.1.2312.9.2.0005.1.2=ASN1:UTF8:pulp-prod-f16
1.3.6.1.4.1.2312.9.2.0005.1.6=ASN1:UTF8:repos/pulp/pulp/fedora-16/x86_64/
" > ${EXTENSION_FILE}



