import asyncio
import time
import math

from .node import Node

class SignalGenerator(Node):
    def __init__(self, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.ports['output'] = {'mode': 'output', 'value': 3.14, 'connections':[]}
        self.period = 3.
        self.offset = 1.
        self.amplitude = 100
        self.output_task_id = self.env.loop.create_task(self.output_task())

    def compute(self):
        self.ports['output']['value'] = self.amplitude * math.sin((time.time() - self.offset) * (math.pi * 2 / self.period))

    async def output_task(self):
        while True:
            #self.debug(str(self.name) + " : output_task...")
            await asyncio.sleep(.03)
            self.compute()
            for cnx in self.ports['output']['connections']:
                if 'update' in cnx:
                    await cnx['prx_dst'].input.put({'qid':cnx['qid'], 'reply':int(self.ports['output']['value'])})
            #self.debug(str(self.name) + " : output_task done.")
#    def query_handle(self, query):
#        pass
