import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataProcess0(DataProcess):
    tagname = "data_process_0"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('config', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.process, gets=['config','input'], returns=['output'])

    async def process(self, config, data, args={}):
        self.debug('config: '+str(config))
        self.debug('data: '+str(data))
        #self.debug('data[0]: '+str(data[0])+' args: '+str(args))
        #value = float(line[1][7:])
        #self.debug('value: '+str(value))
        labels = []
        datasets = [{'borderWidth':1, 'borderColor':'black', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'green', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'blue', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'red', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'magenta', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'cyan', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'borderWidth':1, 'borderColor':'orange', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},]

        labels = list(data.index.map(lambda a:a.timestamp()))
        datasets[0]['data'] = list(data[1])
        datasets[1]['data'] = list(data[2])
        datasets[2]['data'] = list(data[3])
        datasets[3]['data'] = list(data[4])
        datasets[4]['data'] = list(data[5])
        datasets[5]['data'] = list(data[6])
        datasets[6]['data'] = list(data[4] - data[3])

        response = {'labels':labels, 'datasets':datasets}
        return response
