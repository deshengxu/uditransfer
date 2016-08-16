#!/usr/bin/env python
'''uditransfer module: '''

from __future__ import generators
import sys

sys.path.append(".")

try:
    from . import util
except:
    import util

__version__ = "0.01"
__author__ = [
    "Desheng Xu <dxu@ptc.com>"
]
__license__ = "PTC Only"
__contributors__ = "Neil, Brian "

print("This is a test string from init.py at module level")


if __name__ == "__main__":
    print("This is a test string my main at module level.")
    print("Start to call util.py now")
    util.test_print()
