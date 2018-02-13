from .application import *
from .subprocessus import *
from .html_page import *

class DemoApplication(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'name' in kwargs:
            del kwargs['name']
        self["homepage"] = HtmlPage(name="homepage", appname="demo", **kwargs)
        self["extapp"] = Subprocessus("heavyapp", name = "heavyapp", **kwargs)

        self["extapp"].connect(self["homepage"])

    async def msg_handle(self, msg):
        if 'query' in msg and msg['query'] == 'get':
            #self.debug('delegating...'+str(msg))
            await self.delegate(self['homepage'], msg)
            #self.debug('delegated.')
        else:
            await super().msg_handle(msg)
