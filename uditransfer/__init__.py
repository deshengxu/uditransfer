#!/usr/bin/env python
'''uditransfer module: '''

from __future__ import generators
import sys

sys.path.append(".")

try:
    from . import util
except:
    import util

__version__ = "0.3"
__author__ = [
    "Desheng Xu <dxu@ptc.com>"
]
__license__ = "PTC Only"
__contributors__ = "Neil, Brian "


#logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
#rootLogger = logging.getLogger()

#fileHandler = logging.FileHandler("{0}/{1}.log".format(os.path.abspath("./logs/"), "uditransfer.log"))
#fileHandler.setFormatter(logFormatter)
#rootLogger.addHandler(fileHandler)

#consoleHandler = logging.StreamHandler()
#consoleHandler.setFormatter(logFormatter)
#rootLogger.addHandler(consoleHandler)
