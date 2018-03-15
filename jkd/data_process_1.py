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

        # 1 - get input data and put it in a pandas DataFrame (table)
        response = data
        src = pd.DataFrame([i[1] for i in data], index = [pd.datetime.fromtimestamp(i[0]) for i in data])
        return src
