import asyncio
import time
import datetime
import math

from .node import Node

class TextParser(Node):
    tagname = "text_parser"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        #self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])
        self.task_add('process_loop', coro = self.output_task, needs=['input'], provides=['output'])

    async def parse(self, line):
        #TODO
        #self.debug('line: '+str(line[1]))
        value = float(line[1][7:])
        #self.debug('value: '+str(value))
        return "#" * int(100. * (value + 100) / 200.)

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            line = await self.port_read('input')
            value = await self.parse(line)
            await self.port_value_update('output', value)
