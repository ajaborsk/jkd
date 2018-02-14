#from jinja2 import Environment, PackageLoader, select_autoescape

import jinja2

from .node import *

class HtmlPage(Node):
    def __init__(self, elt = None, parent = None, **kwargs):
        if 'appname' in kwargs:
            self.appname = kwargs['appname']
        else:
            self.appname = '.'
        if 'title' in kwargs:
            self.pagetitle = kwargs['title']
        else:
            self.pagetitle = 'Default page title'
        super().__init__(env = kwargs['env'], parent = parent, name = kwargs['name'])
        self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.appname + '/templates/'),
                autoescape=jinja2.select_autoescape(['html', 'xml']))
        
        self.ports['html'] = {'mode':'output'}

        self.parts = []
        for part in elt:
            self.debug(" Page part: {}".format(part.tag))
            #self.parts.append({'template':self.jinja_env.get_template(part.attrib['template'] + '.jinja2')})


    async def msg_handle(self, msg):
        if 'query' in msg and msg['query'] == 'get':
            template = self.jinja_env.get_template(self.name + '.jinja2')
            html_page = template.render({'pagetitle':self.pagetitle, 'name':'Joris'})
            #self.debug("handling"+str(msg))
            #self.debug("Reply to " + str(msg['src']) + "/ qid=" + str(msg['qid']))
            rep= {'qid':msg['qid'], 'reply':html_page}
            #self.debug("Reply = " + str(rep))
            #self.debug("Queue = " + str(msg['src'].input))
            await msg['src'].input.put(rep)
            #self.debug("Replied")
        else:
            await super().msg_handle(msg)

