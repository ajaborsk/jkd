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

