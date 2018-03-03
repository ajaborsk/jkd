import serial
#import serial.aio
import asyncio

from .node import *

class SerialTransport(asyncio.Transport):
    def __init__(self, loop, protocol, serial_instance):
        self._loop = loop
        self._protocol = protocol
        self.serial = serial_instance
        self._closing = False
        self._paused = False
        # XXX how to support url handlers too
        self.serial.timeout = 0
        self.serial.nonblocking()
        loop.call_soon(protocol.connection_made, self)
        # only start reading when connection_made() has been called
        loop.call_soon(loop.add_reader, self.serial.fd, self._read_ready)

    def __repr__(self):
        return '{self.__class__.__name__}({self._loop}, {self._protocol}, {self.serial})'.format(self=self)

    def close(self):
        if self._closing:
            return
        self._closing = True
        self._loop.remove_reader(self.serial.fd)
        self.serial.close()
        self._loop.call_soon(self._protocol.connection_lost, None)

    def _read_ready(self):
        data = self.serial.read(1024)
        if data:
            self._protocol.data_received(data)

    def write(self, data):
        self.serial.write(data)

    def can_write_eof(self):
        return False

    def pause_reading(self):
        if self._closing:
            raise RuntimeError('Cannot pause_reading() when closing')
        if self._paused:
            raise RuntimeError('Already paused')
        self._paused = True
        self._loop.remove_reader(self._sock_fd)
        if self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self):
        if not self._paused:
            raise RuntimeError('Not paused')
        self._paused = False
        if self._closing:
            return
        self._loop.add_reader(self._sock_fd, self._read_ready)
        if self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    #~ def set_write_buffer_limits(self, high=None, low=None):
    #~ def get_write_buffer_size(self):
    #~ def writelines(self, list_of_data):
    #~ def write_eof(self):
    #~ def abort(self):


async def create_serial_connection(loop, protocol_factory, *args, **kwargs):
    ser = serial.Serial(*args, **kwargs)
    print("Opened", flush=True)
    protocol = protocol_factory()
    print("protocol: ", protocol, flush=True)
    transport = SerialTransport(loop, protocol, ser)
    print("transport: ", transport, flush=True)
    return (transport, protocol)


class Output(asyncio.Protocol):
    # def __init__(self, loop, protocol, serial_instance):
        # print("protocol factory __init__()", flush=True)
        # super().__init__(loop, protocol, serial_instance)

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport, flush=True)
        transport.serial.rts = False
        transport.write(b'hello world\n')

    def data_received(self, data):
        print('data received', repr(data), flush=True)
#        self.transport.close()

    def connection_lost(self, exc):
        print('port closed', flush=True)
        # Sure ?? Shouldn't use my own loop reference ??
#        asyncio.get_event_loop().stop()


class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None, elt = None):
        super().__init__(env, parent, name)

        self.ports['output'] = {'mode': 'output', 'value': "", 'connections':[]}
        self.serial_port = "/dev/ttyUSB0"
        self.serial = serial.Serial(self.serial_port, baudrate=57600)
        #self.debug(""+str(s.read()))
        # s.close()
        self.serial.timeout = 0
        self.serial.nonblocking()
        self.current_buffer = b''

        self.env.loop.add_reader(self.serial.fd, self._read_ready)
#        self.env.loop.call_soon(self.env.loop.add_reader, self.serial.fd, self._read_ready)

        #coro = create_serial_connection(self.env.loop, Output, self.serial_port, baudrate=57600)
        #self.task_add('reader', coro = coro, autolaunch = True, provides = ['output'])
        #self.debug('coro= '+str(coro))
        #self.output_task_id = self.env.loop.create_task(coro)
        #self.debug('task= '+str(self.output_task_id))

        # async def reader(self):
        # #TODO: output_task scheduling should be determined by output channels configurations
        # self.serial = serial.Serial(self.serial_port)
        # while True:
            # await asyncio.sleep(0.1)

    async def serial_message_handle(self, serial_buffer):
        self.debug("Serial message: "+str(serial_buffer))

    def _read_ready(self):
        block = self.serial.read(1024)
        self.debug('read:'+str(block))
        for byte in block:
            self.current_buffer += bytes([byte])
            if byte == ord(b'\n'):
                self.env.loop.create_task(self.serial_message_handle(self.current_buffer))
                self.current_buffer = b''

