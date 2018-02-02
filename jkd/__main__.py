import sys

import jkd
from jkd.logging import *

import logging
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s:%(name)s.%(module)s - %(levelname)s : %(message)s"))
logger.addHandler(log_handler)


if len(sys.argv) <= 1:
    environment = jkd.Environment()
    environment.http_serve()
elif sys.argv[1] == 'http':
    environment = jkd.Environment()
    environment.http_serve()
elif sys.argv[1] == 'batch':
    if len(sys.argv) == 3:
        app_name = sys.argv[2]
        #TODO
        print("application result : blabla...")
    else:
        logger.warning("Batch mode : No application name provided")
elif sys.argv[1] == 'slave':
    if len(sys.argv) == 3:
        app_name = sys.argv[2]
        #TODO
        print("(sub)application result : blabla...")
    else:
        logger.warning("Slave : No (sub)application name provided")
else:
    logger.warning("Unknown command")


