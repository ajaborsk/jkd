import asyncio
import time
import datetime
import math
import pandas as pd

from .node import Node
from .data_process import DataProcess

class DataTableToPlotlyjs(DataProcess):
    tagname = "data_table_to_plotlyjs"
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
                for axis in branch:
                    self.axes[axis.get('name')] = {'pos':axis.get('pos'), 'label':axis.get('label')}
            elif branch.tag == 'datasets':
                for dataset in branch:
                    self.datasets.append({'data':dataset.get('data'), 'axis':dataset.get('axis'), 'color':dataset.get('color'), 'type':dataset.get('type'), 'label':dataset.get('label')})

    async def process(self, config, data, args={}):
        self.debug('config: '+str(config))
        self.debug('data: '+str(data))
        #self.debug('data[0]: '+str(data[0])+' args: '+str(args))
        #value = float(line[1][7:])
        #self.debug('value: '+str(value))
        #options = {}
        layout = {}

        y_axes = []
        y_idx = 1
        position = 0.01
        for axis in self.axes:
            if axis[0] == 'y':
                if y_idx == 1:
                    y_idxt = ''
                    self.axes[axis]['y_idxt'] = None
                else:
                    y_idxt = str(y_idx)
                    self.axes[axis]['y_idxt'] = 'y' + str(y_idx)
                layout['yaxis' + y_idxt] = { 'title': self.axes[axis].get('label',''),
                                             'side': 'left',
                                             'position': position,
                                           }
                if y_idxt:
                    layout['yaxis' + y_idxt]['overlaying'] = 'y'
                y_idx += 1
                position += 0.035

        self.debug(''+repr(y_axes))

        # options= {'tooltips': { 'intersect':False },
                  # 'scales': {
                    # 'xAxes':[{
                      # 'minRotation':45,
                      # 'type': 'time',
                      # 'time':{
                        # 'displayFormats':{
                          # 'millisecond':'HH:mm:ss.S',
                          # 'second':'HH:mm:ss',
                          # 'minute':'DD-MM HH:mm',
                          # 'hour':'DD-MM HH:mm',
                          # 'day':'DD-MM HH:mm',
                          # 'week':'DD-MM-YYYY',
                          # 'month':'MM-YYYY',
                          # 'quarter':'MM-YYYY',
                          # 'year':'YYYY'},
                         # 'tooltipFormat':'DD-MM-YYYY HH:mm:ss.S'}}],
                    # 'yAxes': y_axes },
                  # 'zoom':{'enabled':True, 'mode':'y'},
                  # 'pan':{'enabled':True, 'mode':'y'},
                  # 'chartArea': {'backgroundColor': 'rgb(255, 255, 255)'}}

        layout.update({'margin':{'t':20, 'b':20, 'l':20, 'r':20}})

        # time labels => unix timestamp * 1000
        labels = []
        labels = list(data.index.map(lambda a:str(a)))

        # datasets
        # datasets = [{'label':'V Bat', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'blue', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # {'label':'V Cir', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'red', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # {'label':'V Int', 'yAxisID':'voltage', 'borderWidth':1, 'borderColor':'black', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # {'label':'T Ext ', 'yAxisID':'temp', 'borderWidth':1, 'borderColor':'magenta', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # {'label':'T Mcu', 'yAxisID':'temp', 'borderWidth':1, 'borderColor':'cyan', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # {'label':'I Bat', 'yAxisID':'intensity', 'borderWidth':1, 'borderColor':'orange', 'fill':False, 'pointRadius':0, 'lineTension':0, 'data':[]},
                    # ]

        # datasets[0]['data'] = list(data['v_bat'])
        # datasets[1]['data'] = list(data['v_cir'])
        # datasets[2]['data'] = list(data['v_int'])
        # datasets[3]['data'] = list(data['t_ext'])
        # datasets[4]['data'] = list(data['t_mcu'])
        # datasets[5]['data'] = list(data['i_bat'])

        datasets = []
        for dataset in self.datasets:
            datasets.append({'name':dataset['label'],'x':labels, 'y':list(data[dataset['data']]), 'type':'scatter'})
            if self.axes[dataset['axis']]['y_idxt'] is not None:
                datasets[-1]['yaxis'] = self.axes[dataset['axis']]['y_idxt']

        response = {'data':datasets, 'layout':layout}
        self.debug('response: '+str(response))

        return response
