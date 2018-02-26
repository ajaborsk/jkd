import serial

from .node import *

class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None):
        super().__init__(env, parent, name)

        self.ports['output'] = {'mode': 'output', 'value': "", 'connections':[]}
        self.serial_port = "/dev/ACM0"
        self.output_task_id = self.env.loop.create_task(self.output_task())

    async def output_task(self):
        #TODO: output_task scheduling should be determined by output channels configurations
        while True:
            await asyncio.sleep(0.1)

