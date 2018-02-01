# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:46:14 2018

"""
from .container import *

class Application(Container):

    def __init__(self, appname = None, content = None, **kwargs):
        super().__init__(content = content, **kwargs)
        if appname is not None:
            # load application description
            pass
        else:
            # brand new application
            # Add some default nodes :
            # - editor
            # - main page
            pass
