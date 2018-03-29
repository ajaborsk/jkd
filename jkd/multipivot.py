import asyncio
import time
import datetime
import math

from .data_process import DataProcess

class Multipivot(DataProcess):
    tagname = "multipivot"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])

    async def parse(self, line, args={}):
        value = 1.
        return "#" * int(100. * (value + 100) / 200.)
