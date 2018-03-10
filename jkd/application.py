# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:46:14 2018

"""

from .container import *

class Application(Container):
    tagname = "application"
    def __init__(self, elt=None, **kwargs):
        super().__init__(elt=elt, **kwargs)

    def fqn(self):
        return '/' + self.name

