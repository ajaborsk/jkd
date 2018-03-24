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
        layout = {}

        ny_axes = 0
        for axis in self.axes:
            if axis[0] == 'y':
                ny_axes += 1
        height = 1. / ny_axes

        self.debug("height" + str(height))

        y_axes = []
        y_idx = 1
        position = -0.21
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
                                             'domain':[(y_idx - 1) * height + 0.01, y_idx * height - 0.01]
                                           }
                #if y_idxt:
                #    layout['yaxis' + y_idxt]['overlaying'] = 'y'
                y_idx += 1
                position += 0.035

        self.debug(''+repr(y_axes))

        layout.update({'plot_bgcolor':'#fff', 'paper_bgcolor':'#eee', 'legend':{'bgcolor':'#fff'}, 'margin':{'t':10, 'b':40, 'l':50, 'r':10}})

        # time labels
        labels = []
        labels = list(data.index.map(lambda a:str(a)))

        datasets = []
        for dataset in self.datasets:
            datasets.append({'name':dataset['label'],'x':labels, 'y':list(data[dataset['data']]), 'type':'scatter'})
            if self.axes[dataset['axis']]['y_idxt'] is not None:
                datasets[-1]['yaxis'] = self.axes[dataset['axis']]['y_idxt']

        response = {'data':datasets, 'layout':layout}
        self.debug('response: '+str(response))

        return response
