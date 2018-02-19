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
            tree = ET.parse(self.name + '/' + self.name + '.xml')
            self.debug(self.name+ ' application etree loaded')
            root = tree.getroot()
            self.debug("Root :"+str(root.tag)+' '+str(root.attrib))
            self.populate(root)
        except Exception as ex:
            self.warning('unable to load {} application description : {}'.format(self.name, str(ex)))

        # if there is a homepage in the container => /application
        #   then delegate any queries on 'html' port
        if 'homepage' in self:
            self.ports['html'] = {'delegate':self['homepage']}

    def fqn(self):
        return '/' + self.name

    async def _query_handle(self, query):
        self.debug('Application: handling query: '+str(query))
        if 'homepage' in self:
            # Delegate "get" query (= http) to homepage, if it exists
            await self.delegate(self['homepage'], query)
        else:
            # Default (very) basic reply
            await self.msg_send(msg['src'], {"dst":query['src'], 'lcid':query['lcid'], 'eoq':True, "reply":'Default Application "{}" Reply'.format(self.name)})

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
