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
