import asyncio
import time
import datetime
import math

from .node import Node

class History(Node):
    tagname = "data_process"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', autolaunch = True, coro = self.historize, needs=['input'], provides=[])

    async def historize(self):
        self.ports['input']['queue'] = asyncio.Queue(maxsize=5)
        while True:
            data = await self.port_read('input')
            self.debug('data: '+str(data))

