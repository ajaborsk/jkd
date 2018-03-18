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
#        self.port_add('input', mode = 'input')
        self.port_add('calib_data', mode = 'input')
        self.port_add('model', mode = 'input')
        self.port_add('output', cached = True)
        self.task_add('process', coro = self.process, gets=['model', 'calib_data'], returns=['output'])

    async def process(self, model, calib_data, args={}):
        self.debug('model: '+str(model))
        #self.debug('data: '+str(data))
        self.debug('calib_data: '+str(calib_data))

        vbat_idx = []
        vbat_cols = []
        for event in calib_data:
            if event[1]['mode'] == 'ponctual':
                 if event[1]['constraint'] == 'Vbat':
                    vbat_idx.append(pd.datetime.fromtimestamp(event[0]))
                    vbat_cols.append(float(event[1]['constraint-value']))

        vbat_cal= pd.Series(vbat_cols, index=vbat_idx)

        pass

        work = "Calibration result:\n"
        work = "  Calibration data vbat:\n"
        work += vbat_cal.to_string()

        return work
