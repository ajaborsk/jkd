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
        try:
            etree = ET.parse(self.name + '/' + self.name + '.xml')
            self.debug(self.name+ ' application etree loaded')
        except:
            self.warning('unable to load {}s application description'.format(self.name))

    async def msg_handle(self, msg):
        self.debug('Application: handling msg'+str(msg))
        if 'query' in msg and msg['query'] == 'get':
            if 'homepage' in self:
                # Delegate "get" query (= http) to homepage, if it exists
                await self.delegate(self['homepage'], msg)
            else:
                # Default (very) basic reply
                await msg['src'].input.put({"dst":msg['src'], 'qid':msg['qid'], 'eoq':True, "reply":'Default Application "{}s" Reply'.format(self.name)})
        else:
            await super().msg_handle(msg)
