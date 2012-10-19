#!/bin/sh

# Run this script to execute all the unit tests for the RCS
#  or pass in a single argument of the TestCase class name to run just that class
#  Example:
#  $ ./run_tests.sh ProductUsageTest


TO_TEST="entitlement"
if [ $# -ge 1 ]
then
TO_TEST=${TO_TEST}.$1
fi

python src/splice/manage.py test ${TO_TEST} --settings=checkin_service.settings_unittests

