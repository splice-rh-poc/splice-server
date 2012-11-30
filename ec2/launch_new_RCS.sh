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
SSH_KEY="/git/cloude/splice/aws/ssh-keys/splice_rsa.pub"
SSH_USERNAME="root"

AMI_ID="ami-cc5af9a5"
KEY_NAME="splice"
INSTANCE_TYPE="m1.large"
ZONE="us-east-1d"
SEC_GROUP="devel-testing"
VOLUME_SIZE="25"

if [ "${EC2_PRIVATE_KEY}" = "" ] || [ "${EC2_CERT}" = "" ]; then
    echo "EC2_PRIVATE_KEY and EC2_CERT are required.  Please set these env variables and retry" 1>&2
    exit 1
fi

if [ ! -f ${SSH_KEY} ]; then
    echo "Please edit SSH_KEY so it points to the SSH key matching 'KEY_NAME'"
    exit 1
fi

 
RUN_OUTPUT=$(ec2-run-instances ${AMI_ID} -k ${KEY_NAME} --instance-type ${INSTANCE_TYPE} -z ${ZONE} -g ${SEC_GROUP})
INSTANCE_ID=$(echo "$RUN_OUTPUT" | awk '/^INSTANCE/ {print $2}')
echo "Launched '${INSTANCE_ID}' a '${INSTANCE_TYPE}' instance in '${ZONE}' with AMI: '${AMI_ID}', security group '${SEC_GROUP}', and SSH key '${KEY_NAME}'"


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
# Wait for ssh to come up
#
OVER=0
TESTS=0
MAX_CONNECTS=6
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
    echo "Cannot connect to ${NAME}" 1>&2
fi


# Need to get volume id
VOLUME_OUT=`ec2-create-volume --size ${VOLUME_SIZE} --availability-zone ${ZONE}`
VOLUME_ID=`echo "${VOLUME_OUT}" | awk '/^VOLUME/ {print $2}'`
echo "Volume '${VOLUME_ID}' has been created."
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

#
# Tag this instance so it's easier to see from AWS web console
#
ec2-create-tags ${VOLUME_ID} ${INSTANCE_ID} --tag "Name=RCS ${INSTANCE_ID}" &> /dev/null

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

echo ""
echo "**"
echo "**"
echo "Completed Splice install on: ${NAME}"

