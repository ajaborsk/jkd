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

#self.port_add('output', cached = False, timestamped = True)
#self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])

    async def process(self, line):
        return self.data

