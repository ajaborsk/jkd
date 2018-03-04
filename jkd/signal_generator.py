import asyncio
import time
import datetime
import math

from .node import Node

class SignalGenerator(Node):
    tagname = "signal_generator"
    def __init__(self, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.port_add('output', cached = True, timestamped = True)
        self.period = 2.32768
        self.offset = 1.
        self.amplitude = 100
        self.task_add('signal', coro = self.output_task, provides=['output'])

    def compute(self):
        return self.amplitude * math.sin((time.time() - self.offset) * (math.pi * 2 / self.period))

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            value = self.compute()
            await self.port_value_update('output', value)
            await asyncio.sleep(0.1)
