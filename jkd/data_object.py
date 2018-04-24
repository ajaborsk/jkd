import asyncio
import time
import datetime
import math
import json

from .node import Node

class DataObject(Node):
    tagname = "data_object"
    def __init__(self, elt = None, persistent = False, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.persistent = persistent
        self.data = {}
        self.port_add('data', cached = False, timestamped = False)
        self.task_add('data', self.get_data, returns=['data'], client = [])
        if self.persistent:
            fqn = self.fqn().split('/')[1:]
            self.filename = fqn[0] + '/var/' + '.'.join(fqn)
            # load data from file
            try :
                with open(self.filename, "r") as f:
                    self.data = json.load(f)
            except FileNotFoundError:
                self.data = {}

    async def port_write(self, portname, value):
        self.debug(str(portname)+str(' <<== ')+str(value))
        splitted = portname.split(sep='.')
        touched = False
        if splitted[0] == 'data':
            root = self.data
            path = splitted[1:]
            path_len = len(path)
            for idx in range(path_len - 1):
                if path[idx] in root:
                    root = root[path[idx]]
                else:
                    root[path[idx]] = {}
                    root = root[path[idx]]
                    touched = True
            self.debug(str(path))
            #TODO+++ : check this part (first hypothesis) !!!
            if path == []:
                root = value
            else:
                root[path[-1]] = value
            touched = True
        if self.persistent and touched:
            with open(self.filename, "w") as f:
                self.debug(repr(self.data))
                json.dump(self.data, f)

    def port_get(self, portname, args={}):
        if portname in self.ports and len(args) == 0:
            return self.ports[portname]
        else:
            splitted = portname.split(sep='.')
            self.debug('Splitted: ' + str(splitted))
            touched = False
            if splitted[0] == 'data':
                root = self.data
                path = splitted[1:]
                path_len = len(path)
                for idx in range(path_len):
                    if path[idx] in root:
                        root = root[path[idx]]
                    else:
                        root[path[idx]] = {}
                        root = root[path[idx]]
                        touched = True
                ref_port = self.ports['data']
                self.port_add(portname, mode = ref_port['mode'], cached = ref_port['cached'], timestamped = ref_port['timestamped'], auto = True, client = root)
                self.task_add(portname, self.get_data, returns=[portname], client = path)
                #HACK => add manually the port provider... !
                self.ports[portname]['returned_by'] = portname
                if self.persistent and touched:
                    with open(self.filename, "w") as f:
                        json.dump(self.data, f)
                return self.ports[portname]
            else:
                self.warning("port '" + str(portname)+ "' does not exist")
                return None

    async def get_data(self, args={}, client = None):
        root = self.data
        for elt in client:
            root = root[elt]
        return root
