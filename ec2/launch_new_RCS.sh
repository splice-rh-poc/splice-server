#!/bin/sh
#
# Reusing code from: http://stackoverflow.com/questions/2644742/getting-id-of-an-instance-newly-launched-with-ec2-api-tools
#
# Overview
# 1) Provision a EC2 Instance
# 2) Create an EBS volume and attach to instance
# 3) Setup mongodb to use new volume
# 4) wget install script
# 5) run install script to install splice & dependencies
SSH_USERNAME="root"
AMI_ID="ami-cc5af9a5"
KEY_NAME="splice"
INSTANCE_TYPE="m1.large"
ZONE="us-east-1d"
SEC_GROUP="devel-testing"
VOLUME_SIZE="25"

function check_env () {
    if [ ! -f $2 ]; then
        echo "Bad environment variable: $1=$2"
        exit 1
    fi
}

if [ "${CLOUDE_GIT_REPO}" = "" ]; then
    echo "Warning:  The cloude git repository environment variable CLOUDE_GIT_REPO was not set"
    echo "          If you want this script to set environment variables for you," 
    echo "          please re-run with CLOUDE_GIT_REPO set to the correct location"
    echo ""
fi

if [ "${EC2_CERT}" = "" ]; then
    export EC2_CERT=${CLOUDE_GIT_REPO}/splice/aws/X.509/devel/cert-UZC2CZPCLKKV73IBKR6JCYA7VA4JNA5X.pem
fi
check_env "EC2_PRIVATE_KEY" ${EC2_PRIVATE_KEY}

if [ "${EC2_PRIVATE_KEY}" = "" ]; then
    export EC2_PRIVATE_KEY=${CLOUDE_GIT_REPO}/splice/aws/X.509/devel/pk-UZC2CZPCLKKV73IBKR6JCYA7VA4JNA5X.pem
fi
check_env "EC2_CERT" ${EC2_CERT}

if [ "${SSH_KEY}" = "" ]; then
    export SSH_KEY=${CLOUDE_GIT_REPO}/splice/aws/ssh-keys/splice_rsa.pub
fi
check_env "SSH_KEY" ${SSH_KEY}

if [ "${CERTMAKER_DATA}" = "" ]; then
    export CERTMAKER_DATA=${CLOUDE_GIT_REPO}/splice/sample-data/sample-certgen-products.json
fi
check_env "CERTMAKER_DATA" ${CERTMAKER_DATA}


echo "Environment Variables Used:"
echo "CLOUDE_GIT_REPO=${CLOUDE_GIT_REPO}"
echo "EC2_CERT=${EC2_CERT}"
echo "EC2_PRIVATE_KEY=${EC2_PRIVATE_KEY}"
echo "SSH_KEY=${SSH_KEY}"
echo "CERTMAKER_DATA=${CERTMAKER_DATA}"
echo ""
 
RUN_OUTPUT=$(ec2-run-instances ${AMI_ID} -k ${KEY_NAME} --instance-type ${INSTANCE_TYPE} -z ${ZONE} -g ${SEC_GROUP})
INSTANCE_ID=$(echo "$RUN_OUTPUT" | awk '/^INSTANCE/ {print $2}')
echo "Launched '${INSTANCE_ID}' a '${INSTANCE_TYPE}' instance in '${ZONE}' with AMI: '${AMI_ID}', security group '${SEC_GROUP}', and SSH key '${KEY_NAME}'"

# Allow a few seconds for the APIs to all register we launched a new instance
# Have seen a timing problem in past where ec2-describe-instances returns bad data for a newly launched instance
sleep 5
#
# Wait for instance to come up
#
OVER=0
TESTS=0
MAX_TESTS=6
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    description=$(ec2-describe-instances ${INSTANCE_ID})
    STATE=$(echo "$description" | awk '/^INSTANCE/ {print $6}')
    NAME=$(echo "$description" | awk '/^INSTANCE/ {print $4}')
    if [ "$NAME" = "" ]; then
        echo "No instance ${INSTANCE_ID} available. Crashed or was terminated." 1>&2
        exit 1
    fi
    if [ $STATE = "running" ]; then
        OVER=1
    else
        # I like bc but 'echo $(( TESTS+=1 ))' should work, too. Or expr.
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for Instance to start:  Instance: ${INSTANCE_ID}, Name: ${NAME}, State: ${STATE}"
        sleep 5
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "${INSTANCE_ID} never got to running state after waiting 30 seconds" 1>&2
    ec2-terminate-instances ${INSTANCE_ID}
    exit 1
fi
echo "$INSTANCE_ID is running, name is $NAME, will now wait for SSH access to come up"

#
# Create Volume
#
VOLUME_OUT=`ec2-create-volume --size ${VOLUME_SIZE} --availability-zone ${ZONE}`
VOLUME_ID=`echo "${VOLUME_OUT}" | awk '/^VOLUME/ {print $2}'`
echo "Volume '${VOLUME_ID}' has been created."

#
# Tag this instance & volume so it's easier to see from AWS web console
#
ec2-create-tags ${VOLUME_ID} ${INSTANCE_ID} --tag "Name=RCS ${NAME}" &> /dev/null

#
# Wait for ssh to come up
#
OVER=0
TESTS=0
MAX_CONNECTS=12
COMMANDS="(uname -a)"
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_CONNECTS ]; do
    ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "${COMMANDS}" &> /dev/null
    if [ $? != 255 ]; then
        # It means we connected successfully (even if the remote command failed)
        OVER=1
    else
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for SSH access:  Instance: ${INSTANCE_ID}, Name: ${NAME}, State: ${STATE}"
        sleep 5
    fi
done
if [ $TESTS = $MAX_CONNECTS ]; then
    echo "Cannot connect to ssh service on ${NAME}, waited 60 seconds." 1>&2
    exit 1
fi

#
# Wait for volume to be available
#
OVER=0
TESTS=0
MAX_TESTS=6
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    description=$(ec2-describe-volumes ${VOLUME_ID})
    STATE=$(echo "$description" | awk '/^VOLUME/ {print $5}')
    if [ $STATE = "available" ]; then
        OVER=1
    else
        # I like bc but 'echo $(( TESTS+=1 ))' should work, too. Or expr.
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for volume `${VOLUME_ID}` to be available, current state is: ${STATE}"
        sleep 5
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "'${VOLUME_ID}' did not become 'available' within 30 seconds" 1>&2
    ec2-terminate-instances ${INSTANCE_ID}
    ec2-delete-volume ${VOLUME_ID}
    exit 1
fi


# Attach volume
ec2-attach-volume ${VOLUME_ID} -i ${INSTANCE_ID} -d /dev/sdp
#
# Wait for volume to be attached
#
OVER=0
TESTS=0
MAX_TESTS=6
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    description=$(ec2-describe-volumes ${VOLUME_ID})
    STATE=$(echo "$description" | awk '/^ATTACHMENT/ {print $5}')
    if [ $STATE = "attached" ]; then
        OVER=1
    else
        # I like bc but 'echo $(( TESTS+=1 ))' should work, too. Or expr.
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for volume '${VOLUME_ID}' to be attached to instance: '${INSTANCE_ID}', current state is: '${STATE}'"
        sleep 5
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "'${VOLUME_ID}' never got attached to instance '${INSTANCE_ID}' after waiting 30 seconds" 1>&2
    ec2-terminate-instances ${INSTANCE_ID}
    ec2-delete-volume ${VOLUME_ID}
    exit 1
fi

# Configure the EBS Volume to be deleted when instance terminates
ec2-modify-instance-attribute -b "/dev/sdp"=${VOLUME_ID}:true ${INSTANCE_ID}

#
# Setup EBS volume
#
echo "Setting up EBS volume '${VOLUME_ID}' on '${NAME}'"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "mke2fs -j /dev/xvdt"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "mkdir /data"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "mount /dev/xvdt /data"
#
# Prepare for mongodb to use EBS volume
#
echo "Creating directories for mongodb with EBS volume on ${NAME}"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "mkdir -p /data/var/lib/mongodb"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "ln -s /data/var/lib/mongodb /var/lib/mongodb"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "mkdir -p /data/var/log/mongodb"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "ln -s /data/var/log/mongodb /var/log/mongodb"
#
# Open firewall for 80/443
#
echo "Configuring firewall on ${NAME}"
scp -o "StrictHostKeyChecking no" -i ${SSH_KEY} ./etc/sysconfig/iptables ${SSH_USERNAME}@$NAME:/etc/sysconfig/iptables
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "service iptables restart"
#
# Install Splice
#
echo "Installing splice on ${NAME}"
scp -o "StrictHostKeyChecking no" -i ${SSH_KEY} ./install_rpm_setup.sh ${SSH_USERNAME}@$NAME:~
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "chmod +x ./install_rpm_setup.sh"
ssh -o "StrictHostKeyChecking no" -i ${SSH_KEY} ${SSH_USERNAME}@$NAME "time ./install_rpm_setup.sh &> ./splice_install.log "

# Upload product data to cert-maker
echo "Uploading product data from ${CERTMAKER_DATA} to splice-certmaker on ${NAME}"
OVER=0
TESTS=0
MAX_TESTS=6
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    echo "curl -X POST --data \"product_list=\`cat ${CERTMAKER_DATA}\`\"  http://${NAME}:8080/productlist"
    curl -X POST --data "product_list=`cat ${CERTMAKER_DATA}`"  http://${NAME}:8080/productlist
    if [ $? = 0 ]; then
        OVER=1
    else
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting 30 seconds for splice-certmaker to become available"
        sleep 30
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "Unable to upload a product_list to splice-certmaker at: ${NAME}"
    exit 1
fi

echo ""
echo "**"
echo "**"
echo "Completed Splice install on: ${NAME}"

