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
        ibat_sessions = []
        ibat_current_session = []
        for event in calib_data:
            if event[1]['mode'] == 'ponctual':
                 if event[1]['constraint'] == 'Vbat':
                    vbat_idx.append(pd.datetime.fromtimestamp(event[0]))
                    vbat_cols.append(float(event[1]['constraint-value']))
            elif event[1]['mode'] == 'enter':
                if event[1]['constraint'] == 'Ibat':
                    ibat_current_session = [pd.datetime.fromtimestamp(event[0])]
                    ibat_current_session.append(float(event[1]['constraint-value']))
            elif event[1]['mode'] == 'leave':
                if event[1]['constraint'] == 'Ibat' and len(ibat_current_session) == 2:
                    ibat_current_session.append(pd.datetime.fromtimestamp(event[0]))
                    ibat_sessions.append(ibat_current_session)
                    ibat_current_session = []

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

        ibat_cal = pd.DataFrame()
        for session in ibat_sessions:
            if len(session) == 3:
                start = session[0].timestamp()
                end = session[2].timestamp()
                # get values from history for calibration session
                ivalues = await self.port_input_get("input", {'after': start, 'before': end})
                # convert to pandas DataFrame
                ivalues = pd.DataFrame([i[1] for i in ivalues], index = [pd.datetime.fromtimestamp(i[0]) for i in ivalues])
                ibat_cal = pd.concat([ibat_cal, ivalues])

        alpha_cir = (ibat_cal[4] / (ibat_cal[3] / alpha)).mean()
        await self.msg_query(self.parent, {'method':'put', 'policy':'immediate', 'url':'/demo_pi/model', 'path':'/demo_pi/model', 'port':'data.alpha_cir', 'args':{'value':alpha_cir}})

        work = "Calibration result:<br/>"
        work += "  Calibration data vbat:<br/>"
        work += vbat_cal.to_html()
        work += "alpha: " + str(alpha)
        work += str(ibat_sessions)
        work += "<br/>Calibration data ibat :<br/>"+str(ibat_cal.to_html())

        return work
