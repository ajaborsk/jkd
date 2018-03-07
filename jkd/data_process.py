import asyncio
import time
import datetime
import math

from .node import Node

class DataProcess(Node):
    tagname = "data_process"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.process, gets=['input'], returns=['output'])

    async def process(self, data):
        #self.debug('data: '+str(data))
        result = data
        #self.debug('result: '+str(result))
        return result
