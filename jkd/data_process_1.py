import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataProcess1(DataProcess):
    tagname = "data_process_1"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('model', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.process, gets=['model','input'], returns=['output'])

    async def process(self, model, data, args={}):
        # 'model' input is for model parameters. Model description is this code.
        self.debug('model: '+str(model))
        self.debug('data: '+str(data))

        alpha_bat = 1.5961 # 4.065 * 10944 / 27872
        alpha_cir = 1.5888 # 4.065 * 10944 / 28000

        alpha_bat_from_model = model['alpha_bat']

        # 1 - get input data and put it in a pandas DataFrame (table)
        work = pd.DataFrame([i[1] for i in data], index = [pd.datetime.fromtimestamp(i[0]) for i in data])
        resp = pd.DataFrame()

        # 2 - process...
        #resp['v_bat'] = (alpha_bat / work[1] * work[3]).rolling('10min').mean()
        resp['v_bat'] = (work[3] / alpha_bat_from_model).rolling('10min').mean()
        resp['v_cir'] = (alpha_cir / work[1] * work[4]).rolling('10min').mean()
        #work['v_bat'] = (alpha_bat / work[1] * work[3])
        #work['v_cir'] = (alpha_cir / work[1] * work[4])
        resp['i_bat'] = -(resp['v_cir'] - resp['v_bat']) / 0.1 * 1000 # milli amps
        resp['v_int'] = resp['v_bat'] + resp['i_bat'] / 1000. * 0.40
        resp['t_ext'] = work[6] / 32768. * 25.

        # 21888 => 23°C
        # 21500 => 17°C ~~
        # 388 => 6°C => 65 / °C
        c = 160.
        resp['t_mcu'] = (work[2] - (21888 - 23 * c)) / c

        #self.debug('work: '+str(work))

        return resp
