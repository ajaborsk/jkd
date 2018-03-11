import asyncio
import time
import datetime
import math

from .node import Node

class DataObject(Node):
    tagname = "data_object"
    def __init__(self, elt = None, persistant = False, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.persistent = persistant
        self.data = {}
        self.port_add('data', cached = False, timestamped = False)
        if self.persistant:
            #TODO
            # load data from file
            pass

    def port_get(self, portname):
        if portname in self.ports:
            return self.ports[portname]
        else:
            splitted = portname.rsplit(sep='.', maxsplit=1)
            if len(splitted) == 2 and splitted[0] in self.ports:
                ref_port = self.ports[splitted[0]]
                self.port_add(portname, mode = ref_port['mode'], cached = ref_port['cached'], timestamped = ref_port['timestamped'], auto = True)
                return self.ports[portname]
            else:
                self.warning("port '" + str(portname)+ "' does not exist")
                return None

