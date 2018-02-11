# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:46:14 2018

"""
from .container import *

class Application(Container):

    def __init__(self, appname = None, **kwargs):
        super().__init__(**kwargs)
        if appname is not None:
            # load application description
            pass
        else:
            # brand new application
            # Add some default nodes :
            # - editor
            # - main page
            pass

    async def msg_handle(self, msg):
        print('Application: handling msg'+str(msg))
        if 'src' in msg:
            await msg['src'].input.put({"dst":msg['src'], 'qid':msg['qid'], 'eoq':True, "reply":'Default Application Reply'})
        else:
            await super().msg_handle(msg)
