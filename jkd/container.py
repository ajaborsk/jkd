# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:47:29 2018

"""

from .node import *

class Container(Node):
    tagname = "container"
    def __init__(self, contents = None, **kwargs):
        super().__init__(**kwargs)
        if contents is None:
            # a brand (and empty) new container
            #TODO
            self.contents = {}
            pass
        else:
            # get container content from argument
            #TODO
            pass

    def node_add(self, name, node):
        "Add a named node to the containe"
        #TODO: Check if node already exists
        #TODO: Check node type
        #TODO: Check name type
        self.contents[name] = node

    def get(self):
        #return node content (a list of etree elements)
        #TODO
        return []

    def __setitem__(self, key, value):
        self.contents[key] = value

    def __getitem__(self, key):
        return self.contents[key]

    def __delitem__(self, key):
        del self.contents[key]

    def __contains__(self, key):
        return key in self.contents

