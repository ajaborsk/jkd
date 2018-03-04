import serial
#import serial.aio
import asyncio

from .node import *


class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None, elt = None):
        super().__init__(env, parent, name)

        self.ports['output'] = {'mode': 'output', 'value': "", 'connections':[]}
        self.serial_port = elt.attrib.get('serial_port', "/dev/tty0")
        self.serial_baudrate = int(elt.attrib.get('serial_baudrate', 9600))
        self.serial = serial.Serial(self.serial_port, self.serial_baudrate)
        self.serial.timeout = 0
        self.serial.nonblocking()
        self.current_buffer = b''

        self.env.loop.add_reader(self.serial.fd, self._read_ready)

    async def serial_message_handle(self, serial_buffer):
        self.debug("Serial message: "+str(serial_buffer))

    def _read_ready(self):
        block = self.serial.read(1024)
        #self.debug('read:'+str(block))
        for byte in block:
            self.current_buffer += bytes([byte])
            if byte == ord(b'\n'):
                self.env.loop.create_task(self.serial_message_handle(self.current_buffer))
                self.current_buffer = b''

