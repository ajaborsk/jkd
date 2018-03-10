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
        self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])

    async def process(self, data, args={}):
        return self.data

