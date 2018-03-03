import asyncio
import time
import datetime
import math

from .node import Node

class SignalGenerator(Node):
    tagname = "signal_generator"
    def __init__(self, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.ports['output'] = {'mode': 'output', 'value': 3.14, 'connections':[]}
        self.period = 2.32768
        self.offset = 1.
        self.amplitude = 100
#        self.output_task_id = self.env.loop.create_task(self.output_task())
        self.task_add('signal', coro = self.output_task, provides=['output'])

    def compute(self):
        self.ports['output']['value'] = self.amplitude * math.sin((time.time() - self.offset) * (math.pi * 2 / self.period))

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            #self.debug(str(self.name) + " : output_task...")
            self.compute()
            for cnx in self.ports['output']['connections']:
                if 'update' in cnx:
                    if 'finished' not in cnx or cnx['finished'] == False:
                        flags = 'f'
                        cnx['finished'] = True # Channel opening is finished
                    else:
                        flags = ''
                    if 'count' not in cnx:
                        cnx['count'] = 0
                    else:
                        cnx['count'] += 1
                    msg = {'prx_src':self, 'lcid':cnx['lcid'], 'flags':flags, 'reply':(datetime.datetime.now().timestamp(), int(self.ports['output']['value']))}
                    #self.debug(str(self.name) + " : output_msg to "+str(cnx['prx_dst'])+': '+str(msg))
                    await self.msg_send(cnx['prx_dst'], msg)
                    #self.debug('Queue length: '+str(cnx['prx_dst'].input.qsize()), 'msg')
            #self.debug(str(self.name) + " : output_task done.")
            await asyncio.sleep(0.1)
#    def query_handle(self, query):
#        pass
