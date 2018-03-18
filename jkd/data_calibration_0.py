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

        vbat_cal= pd.DataFrame(vbat_cols, index=vbat_idx, columns=['Vbat'])

        meas = []
        for i in range(len(vbat_cal)):
            ts = vbat_cal.index[i].timestamp()
            # get values from history around calibration timestamp
            values = await self.port_input_get("input", {'after': ts - 180, 'before': ts + 180})
            # convert to pandas DataFrame
            values = pd.DataFrame([i[1] for i in values], index = [pd.datetime.fromtimestamp(i[0]) for i in values])
            # put mean value in calibration dataframe
            meas.append(values[3].mean())
        vbat_cal['meas'] = meas

        vbat_cal['alpha'] = vbat_cal['meas'] / vbat_cal['Vbat']
        alpha = vbat_cal['alpha'].mean()
        vbat_cal['meas_s'] = vbat_cal['Vbat'] * alpha
        vbat_cal['delta_m'] = vbat_cal['meas_s'] - vbat_cal['meas']
        vbat_cal['delta_v'] = vbat_cal['delta_m'] / alpha

        values = await self.port_input_get("input", {'after':1521316500, 'before':1521316520})
        # convert to pandas DataFrame
        values = pd.DataFrame([i[1] for i in values], index = [pd.datetime.fromtimestamp(i[0]) for i in values])

        await self.msg_query(self.parent, {'method':'put', 'policy':'immediate', 'url':'/demo_pi/model', 'path':'/demo_pi/model', 'port':'data.alpha_bat', 'args':{'value':alpha}})



        work = "Calibration result:<br/>"
        work += "  Calibration data vbat:<br/>"
        work += vbat_cal.to_html()
        work += "alpha: " + str(alpha)
        work += "<br/>values :<br/>"+str(values.to_html())

        return work
