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
        #self.task_add('process_loop', coro = self.output_task, needs=['input'], provides=['output'])

    async def process(self, data):
        #TODO
        #self.debug('line: '+str(line[1]))
        result = data
        #self.debug('value: '+str(value))
        return result

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            data = await self.port_read('input')
            result = await self.process(data)
            await self.port_value_update('output', result)
