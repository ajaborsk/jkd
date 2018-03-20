# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 08:55:32 2018

@author: jaborsal06
"""

import asyncio
import time
import datetime
import math

from .data_process import DataProcess

class DataTableToTabulatorjs(DataProcess):
    tagname = "data_process"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('config', mode = 'input')
        #self.port_add('input', mode = 'input')
        #self.port_add('output', cached = True, timestamped = True)
        self.task_add('format', coro = self.format, gets=['config', 'input'], returns=['output'])

    async def format(self, config, data, args={}):
        self.debug("Config: " + str(config))
        #self.debug('data: '+str(data))
        result = {}
        
        result['columns'] = []
        for column in data.columns:
            #TODO: Get title from config
            result['columns'].append({'title':column, 'field':column})
        
        result['data'] = []
        for row_idx in range(len(data)):
            row={'id':row_idx}
            row.update(dict(data.iloc[row_idx]))
            result['data'].append(row)
        
        self.debug('result: '+str(result))
        return result
