import asyncio
import time
import datetime
import math
import json
import struct

from .node import Node

class History(Node):
    tagname = "history"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', autolaunch = True, coro = self.historize, needs=['input'], provides=[])
        self.task_add('history', coro = self.history, gets=[], returns=['output'])

    async def historize(self):
        self.ports['input']['queue'] = asyncio.Queue(maxsize=5)
        fqn = self.fqn().split('/')[1:]
        self.filename = fqn[0] + '/var/' + '.'.join(fqn)
        self.debug('history filename: '+str(self.filename+'.data'))
        self.data_file = open(self.filename+'.data', mode='ab', buffering = 0)
        self.current_pos = self.data_file.tell()
        self.debug('current pos: '+str(self.current_pos))
        self.debug('index filename: '+str(self.filename+'.idx'))
        self.index_file = open(self.filename+'.idx', mode='ab', buffering = 0)
        while True:
            data = await self.port_read('input')
            if data[1] is not None:
                self.debug('data: '+str(data))
                data_bin = json.dumps(data).encode('utf8')
                #self.debug('1: '+str(data))
                pos = self.current_pos
                self.data_file.write(data_bin)
                #self.debug('2: '+str(data))
                self.current_pos = self.data_file.tell()
                size = self.current_pos - pos
                index_bin = struct.pack('QQL', int(data[0]), pos, size)
                #self.debug('3: '+str(data))
                self.index_file.write(index_bin)
                #self.debug('4: '+str(data))

    async def history(self, args = {}):
        result = []
        data_file = open(self.filename+'.data', mode='rb')
        index_file = open(self.filename+'.idx', mode='rb')
        size = struct.calcsize('QQL')
        done = False
        while not done:
            idx_b = index_file.read(size)
            if len(idx_b) == size:
                idx = struct.unpack('QQL', idx_b)
                #self.debug(str(idx))
                data_file.seek(idx[1])
                b_data = data_file.read(idx[2])
                #self.debug(str(b_data))
                data = json.loads(b_data.decode('utf8'))
                result.append(data)
            else:
                done = True
        return result
