import serial
import serial.aio
import asyncio

from .node import *

class Output(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False
        transport.write(b'hello world\n')

    def data_received(self, data):
        print('data received', repr(data))
        self.transport.close()

    def connection_lost(self, exc):
        print('port closed')
        asyncio.get_event_loop().stop()

class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None, elt = None):
        super().__init__(env, parent, name)

        self.ports['output'] = {'mode': 'output', 'value': "", 'connections':[]}
        self.serial_port = "/dev/ACM0"
        coro = serial.aio.create_serial_connection(self.env.loop, Output, self.serial_port, baudrate=115200)
        #self.task_add('reader', coro = coro, autolaunch = True, provides = ['output'])

        #self.output_task_id = self.env.loop.create_task(self.output_task())

    # async def reader(self):
        # #TODO: output_task scheduling should be determined by output channels configurations
        # self.serial = serial.Serial(self.serial_port)
        # while True:
            # await asyncio.sleep(0.1)

