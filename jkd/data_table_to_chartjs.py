import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataTableToChartjs(DataProcess):
    tagname = "data_table_to_chartjs"
    def __init__(self, elt = None, preset=None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('config', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.process, gets=['config','input'], returns=['output'])

        #TODO: use this preset
        self.preset = preset
        self.axes = {}
        self.datasets = []

        for branch in elt:
            if branch.tag == 'axes':
                for axe in branch:
                    self.axes[axe.get('name')] = {'pos':axe.get('pos')}
            elif branch.tag == 'datasets':
                for dataset in branch:
                    self.datasets.append({'data':dataset.get('data'), 'color':dataset.get('color'), 'type':dataset.get('type'), 'label':dataset.get('label')})

    async def process(self, config, data, args={}):
        self.debug('config: '+str(config))
        self.debug('data: '+str(data))
        #self.debug('data[0]: '+str(data[0])+' args: '+str(args))
        #value = float(line[1][7:])
        #self.debug('value: '+str(value))
        options = {}

        labels = []
        datasets = [{'label':'V Bat', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'blue', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'label':'V Cir', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'red', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'label':'V Int', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'black', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'label':'T Ext ', 'yAxisID':'temp', 'borderWidth':1, 'borderColor':'magenta', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'label':'T Mcu', 'yAxisID':'temp', 'borderWidth':1, 'borderColor':'cyan', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    {'label':'I Bat', 'yAxisID':'intensity', 'borderWidth':1, 'borderColor':'orange', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    ]

        # time labels => unix timestamp * 1000
        labels = list(data.index.map(lambda a:a.timestamp()*1000))

        # datasets
        datasets[0]['data'] = list(data['v_bat'])
        datasets[1]['data'] = list(data['v_cir'])
        datasets[2]['data'] = list(data['v_int'])
        datasets[3]['data'] = list(data['t_ext'])
        datasets[4]['data'] = list(data['t_mcu'])
        datasets[5]['data'] = list(data['i_bat'])

        response = {'data':{'labels':labels, 'datasets':datasets}}
        self.debug('response: '+str(response))
        return response
