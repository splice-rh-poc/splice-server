#!/usr/bin/env python

SUB_MGR_PATH="/usr/share/rhsm"
import sys
sys.path.append(SUB_MGR_PATH)

from subscription_manager.facts import Facts
def get_facts():
    return Facts().get_facts()

if __name__ == "__main__":
    print get_facts()
