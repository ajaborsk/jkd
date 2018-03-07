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
        self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])

    async def parse(self, line):
        #self.debug('line: '+str(line[1]))
        value = float(line[1][7:])
        #self.debug('value: '+str(value))
        return "#" * int(100. * (value + 100) / 200.)
