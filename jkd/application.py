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
            for child in root:
                self.debug("Child :"+str(child.tag)+' '+str(child.attrib))
                if child.tag in self.env.registry:
                    self[child.attrib['name']] = self.env.registry[child.tag](env=self.env, elt=child, **child.attrib)
                else:
                    self.warning("Application : Unable to instanciate node for '{}' tag".format(child.tag))
        except Exception as ex:
            self.warning('unable to load {} application description : {}'.format(self.name, str(ex)))

    async def msg_handle(self, msg):
        self.debug('Application: handling msg: '+str(msg))
        if 'query' in msg and msg['query'] == 'get':
            if 'homepage' in self:
                # Delegate "get" query (= http) to homepage, if it exists
                await self.delegate(self['homepage'], msg)
            else:
                # Default (very) basic reply
                await msg['src'].input.put({"dst":msg['src'], 'qid':msg['qid'], 'eoq':True, "reply":'Default Application "{}" Reply'.format(self.name)})
        elif 'query' in msg and msg['query'] == 'data':
            await self.delegate(self[msg['dst']], msg)
        else:
            await super().msg_handle(msg)
