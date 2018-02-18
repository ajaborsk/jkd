import sys

import jkd
from jkd.logging import *

import logging
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s:[%(process)s] {main} jkd.%(module)s - %(levelname)s : %(message)s"))
logger_main.addHandler(log_handler)
logger_main.setLevel(logging.DEBUG)

from .node import *

if len(sys.argv) <= 1:
    environment = jkd.EnvHttpServer()
    environment.run()
elif sys.argv[1] == 'http':
    environment = jkd.EnvHttpServer()
    environment.run()
elif sys.argv[1] == 'batch':
    if len(sys.argv) >= 3:
        app_name = sys.argv[2]
        #TODO
        print("application result : blabla...")
    else:
        logger_main.warning("Batch mode : No application name provided")
elif sys.argv[1] == 'slave':
    if len(sys.argv) >= 3:
        app_name = sys.argv[2]
        if len(sys.argv) >= 4:
            logger_main.debug('Arg length = '+str(len(sys.argv[3])))
            logger_main.debug('Arg = '+str(sys.argv[3]))
            tree = ET.fromstring(sys.argv[3])
        else:
            tree = None
            logger_main.warning("Slave mode : No XML definition provided")
        #TODO
        sub = jkd.EnvSubApplication(app_name, tree = tree)
        print("(sub)application result : blabla...", sys.argv[2])
        sub.run()
    else:
        logger_main.warning("Slave : No (sub)application name provided")
else:
    logger_main.error("Unknown command : {:s}".format(sys.argv[1]))


