import serial

from .node import *

class SerialCapture(Node):

    def __init__(self, env = None, parent = None, name = None):
        super().__init__(env, parent, name)

        self.serial_port = "/dev/ACM0"


