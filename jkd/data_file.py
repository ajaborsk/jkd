import asyncio
import time
import datetime
import math

from .node import Node

class DataFile(Node):
    tagname = "data_file"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)

        self.data = None

        self.port_add('output', cached = False, timestamped = True)
        #self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])
        self.task_add('process_loop', coro = self.output_task, provides=['output'])

    async def process(self, line):
        return self.data

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            value = await self.process()
            await self.port_value_update('output', value)
