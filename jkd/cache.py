# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 14:38:12 2018

@author: jaborsal06
"""

import datetime

import asyncio
from .node import *

class Cache(Node):
    tagname = "cache"
    def __init__(self, contents = None, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = None
        self.contents = None
        self.sources = [] # inputs list
        self.subscriptions = [] # output
        self.output = asyncio.Queue()
        self.input = asyncio.Queue()
    
    async def aset(self, value):
        self.contents = value
        self.timestamp = datetime.datetime()
        # triggers 
        #TODO
        
    async def aget(self):
        #TODO
        pass
