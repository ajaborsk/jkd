import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataCalibration0(DataProcess):
    tagname = "data_calibration_0"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('calib_data', mode = 'input')
        self.port_add('model', mode = 'input')
        self.port_add('output', cached = True)
        self.task_add('process', coro = self.process, gets=['model','input', 'calib_data'], returns=['output'])

    async def process(self, model, data, calib_data, args={}):
        self.debug('model: '+str(model))
        self.debug('data: '+str(data))
        self.debug('calib_data: '+str(calib_data))

        work = "Calibration result:\n"

        return work
