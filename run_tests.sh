#!/bin/sh

# Run this script to execute all the unit tests for the RCS
#  or pass in a single argument of the TestCase class name to run just that class
#  Example:
#  $ ./run_tests.sh ProductUsageTest


# Allows Splice configuration files to be override
export SPLICE_CONFIG="`pwd`/src/splice/test_data/splice_unittests.conf"

TO_TEST="entitlement"
if [ $# -ge 1 ]
then
TO_TEST=${TO_TEST}.$1
fi

python src/splice/manage.py test ${TO_TEST} 

