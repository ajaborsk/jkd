
import time
import math

from .node import Node

class SignalGenerator(Node):
    def __init__(self, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.ports['output'] = {'mode': 'output', 'value': 0}
        self.period = 3.
        self.offset = 1.
        self.amplitude = 100

    def compute(self):
        self.ports['output']['value'] = self.amplitude * math.sin((time.time() - self.offset) / (math.PI * 2 * self.period))
