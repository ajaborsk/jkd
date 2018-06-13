import sys
import argparse

import jkd
from jkd.logging import *

import logging
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s:[%(process)s] {%(name)s}/%(levelname)s : %(message)s"))
logger_main.addHandler(log_handler)
logger_main.setLevel(logging.INFO)
logger_msg.addHandler(log_handler)
logger_msg.setLevel(logging.DEBUG)

from .node import *

parser = argparse.ArgumentParser(description='Jkd !')
parser.add_argument('-m', '--mode', type=str, choices = ['httpd','batch','slave'], default='httpd', nargs='?',
                    help='server launch mode')
parser.add_argument('-p', '--port', type=int, default=9080, nargs='?',
                    help='server port')
parser.add_argument('-l', '--launch', type=str, nargs='*', metavar='APPNAME',
                    help='application(s) to launch')
parser.add_argument('root_node', type=str, nargs='?', help='node name for slave mode')
parser.add_argument('xml', type=str, nargs='?', help='xml definition for slave mode')

args = parser.parse_args()

print(args)

if args.mode == 'httpd':
    environment = jkd.EnvHttpServer()
    if args.launch is not None and len(args.launch) > 0:
        for appname in args.launch:
            environment.app_launch(appname)
    environment.run(port=args.port)
elif args.mode == 'batch':
    if args.launch is not None and len(args.launch) > 0:
        app_name = args.launch[0]
        #TODO
        print("application result : blabla...")
    else:
        logger_main.warning("Batch mode : No application name provided")
elif args.mode == 'slave':
    root_name = args.root_node
    xml_def = str(args.xml)
    if xml_def[0] == '"':
        xml_def = xml_def[1:-1]
    logger_main.debug('Arg length = '+str(len(sys.argv[3])))
    logger_main.debug('Arg = ' + xml_def)
    tree = ET.fromstring(xml_def)
#    logger_main.warning("Slave mode : No XML definition provided")
    #TODO
    sub = jkd.EnvSubApplication(root_name, tree = tree)
    print("(sub)application result : blabla...", sys.argv[2])
    sub.run()
#    else:
#        logger_main.warning("Slave : No (sub)application name provided")
else:
    logger_main.error("Unknown command : {:s}".format(sys.argv[1]))


