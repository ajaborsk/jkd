# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:47:29 2018

"""

from .node import *

class Container(Node):
    tagname = "container"
    def __init__(self, content = None):
        super().__init__()
        if content is None:
            # a brand (and empty) new container
            #TODO
            self.nodes = []
            pass
        else:
            # get container content from argument
            #TODO
            pass
        
    def get(self):
        #return node content (a list of etree elements)
        #TODO
        return []
        
