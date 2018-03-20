import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataRawToTable(DataProcess):
    tagname = "data_raw_to_table"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('model', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.process, gets=['model','input'], returns=['output'])
        self.values = []
        for branch in elt:
            if branch.tag == 'values':
                for value in branch:
                    self.values.append({'mode':value.tag, 'name':value.get('name'), 'eval':value.get('eval'), 'unit':value.get('unit'), 'tags':value.get('tags')})
#        self.debug(str(self.values))

    async def process(self, model, data, args={}):
        # 'model' input is for model parameters. Model description is this code.
        # self.debug('model: '+str(model))
        # self.debug('data: '+str(data))

        # 1 - get input data and put it in a pandas DataFrame (table)
        input = pd.DataFrame([i[1] for i in data], index = [pd.datetime.fromtimestamp(i[0]) for i in data])
        value = pd.DataFrame()
        temp = pd.DataFrame()
        my_locals = {'input':input, 'model':model, 'value':value, 'temp':temp}

        # 2 - process...
        for val in self.values:
            #TODO: A more safe eval environment (globals)
            #TODO: Exception handling
            if val['mode'] == 'value':
                value[val['name']] = eval(val['eval'], None, my_locals)
            elif val['mode'] == 'temp':
                temp[val['name']] = eval(val['eval'], None, my_locals)
            elif val['mode'] == 'var':
                my_locals[val['name']] = eval(val['eval'], None, my_locals)

        return value
