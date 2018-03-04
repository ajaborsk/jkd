import asyncio
import time
import datetime
import math

from .node import Node

class LineParser(Node):
    tagname = "line_parser"
    def __init__(self, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('signal', coro = self.output_task, provides=['output'])

    def parse(self, line):
        return {'dummy':1.22}

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            line = await self.port_read('input')
            value = self.parse(line)
            await self.port_value_update('output', value)
