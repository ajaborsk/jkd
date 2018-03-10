# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:46:14 2018

"""

from .container import *

class Application(Container):
    tagname = "application"
    def __init__(self, elt=None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        # try:
            # self.populate(root)
        # except Exception as ex:
            # self.warning('unable to load {} application description : {}'.format(self.name, str(ex)))

        # if there is a homepage in the container => /application
        #   then delegate any queries on 'html' port
        # if 'homepage' in self:
            # self.ports['html'] = {'delegate':self['homepage']}

    def fqn(self):
        return '/' + self.name

    # async def msg_query_handle(self, query):
        # #self.debug('Application: handling query: '+str(query), 'msg')
        # if 'homepage' in self:
            # # Delegate "get" query (= http) to homepage, if it exists
            # await self.msg_queue_delegate(self['homepage'], query)
        # else:
            # # Default (very) basic reply
            # await self.msg_send(msg['src'], {"dst":query['src'], 'lcid':query['lcid'], 'eoq':True, "reply":'Default Application "{}" Reply'.format(self.name)})

    # async def msg_handle(self, msg):
        # self.debug('Application: handling msg: '+str(msg))
        # if 'query' in msg and msg['query'] == 'get':
            # if 'homepage' in self:
                # # Delegate "get" query (= http) to homepage, if it exists
                # await self.delegate(self['homepage'], msg)
            # else:
                # # Default (very) basic reply
                # await msg['src'].input.put({"dst":msg['src'], 'lcid':msg['lcid'], 'eoq':True, "reply":'Default Application "{}" Reply'.format(self.name)})
        # elif 'query' in msg and msg['query'] == 'data':
            # await self.delegate(self[msg['dst']], msg)
        # else:
            # await super().msg_handle(msg)
