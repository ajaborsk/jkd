import asyncio
import time
import datetime
import math

from .node import Node

class Cache(Node):
    tagname = "cache"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)

        self.data = None

        self.port_add('input', mode = 'input')
        self.port_add('output', cached = False, timestamped = True)
        #self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])
        self.task_add('process_loop', coro = self.output_task, needs=['input'], provides=['output'])

    async def process(self, line):
        return self.data

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            input_data = await self.port_read('input')
            value = await self.process(input_data)
            await self.port_value_update('output', value)
