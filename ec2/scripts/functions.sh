#!/bin/sh

# hostname for Splice's rpm builder machine
# used by install scripts to setup up yum repo files
export BUILDER_ADDR=ec2-23-22-86-129.compute-1.amazonaws.com

function waitfor() {
    if [ "$#" -ne 4 ]; then
        echo "Incorrect usage of waitfor() function, only $# arguments passed when 4 were expected"
        echo "Usage: retry CMD WAITING_MESSAGE NUM_ITERATIONS SLEEP_SECONDS_EACH_ITERATION"
        exit 1
    fi
    CMD=$1
    WAITING_MSG=$2
    MAX_TESTS=$3
    SLEEP_SECS=$4
    
    TESTS=0
    OVER=0
    while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
        eval ${CMD} > /dev/null
        if [ $? -eq 0 ]; then
            OVER=1
        else
            TESTS=$(echo $TESTS+1 | bc)
            echo $WAITING_MSG will wait for ${SLEEP_SECS} seconds this is attempt ${TESTS}/${MAX_TESTS} at `date`
            sleep $SLEEP_SECS
        fi
    done
    if [ $TESTS = $MAX_TESTS ]; then
        echo ""
        echo "**ERROR**:"
        echo "Command:  ${CMD}"
        echo "Unsuccessful after ${MAX_TESTS} iterations with a sleep of ${SLEEP_SECS} seconds in between"
        exit 1
    fi
}
