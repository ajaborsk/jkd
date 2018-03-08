import serial
#import serial.aio
import asyncio

from .node import *

#TODO: Find a way to provide a value on a port without any task (use a integrated one)

class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None, elt = None, serial_port="/dev/tty0", serial_baudrate=9600):
        super().__init__(env, parent, name)

        self.ports['output'] = {'mode': 'output', 'value': "", 'connections':[]}
        self.serial_port = serial_port
        self.serial_baudrate = int(serial_baudrate)
        self.serial = serial.Serial(self.serial_port, self.serial_baudrate)
        self.serial.timeout = 0
        self.serial_queue = asyncio.Queue()
        self.serial.nonblocking()
        self.current_buffer = b''
        self.env.loop.add_reader(self.serial.fd, self._read_ready)

        self.task_add('serial_line_handler', coro = self.serial_line_handler, provides = ['output'], autolaunch=True)

    async def serial_line_handler(self):
        while True:
            await self.port_value_update('output', await self.serial_queue.get())

    async def serial_message_handle(self, serial_buffer):
        self.debug("Serial message: "+str(serial_buffer))
        await self.serial_queue.put(serial_buffer)

    def _read_ready(self):
        block = self.serial.read(1024)
        #self.debug('read:'+str(block))
        for byte in block:
            self.current_buffer += bytes([byte])
            if byte == ord(b'\n'):
                self.env.loop.create_task(self.serial_message_handle(self.current_buffer))
                self.current_buffer = b''

