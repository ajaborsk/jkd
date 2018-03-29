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
        self.port_add('output0', cached = True, timestamped = True)
        self.port_add('output1', cached = True, timestamped = True)
        self.task_add('do_it', coro = self.do_it, needs=['input'], provides=['output0', 'output1'])

    async def do_it(self, args={}):
        while True:
            data = await self.port_input_get("input", args)
            self.port_update("output1", data)
    
