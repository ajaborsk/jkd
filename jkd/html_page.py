#from jinja2 import Environment, PackageLoader, select_autoescape

import jinja2

from .node import *

class HtmlPage(Node):
    tagname = "html_page"
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
        self.task_add('generate', coro = self.generate, returns = ['html'])

        self.parts = []
        for part in elt:
            self.debug("  Page part: {}".format(part.tag))
            #self.parts.append({'template':self.jinja_env.get_template(part.attrib['template'] + '.jinja2')})

    async def generate(self):
        template = self.jinja_env.get_template(self.name + '.jinja2')
        html_page = template.render({'pagetitle':self.pagetitle, 'name':'Joris'})
        return html_page

    async def msg_query_handle(self, msg):
        self.debug(str(msg), 'msg')
        if 'query' in msg and msg['query'] == 'get':
            template = self.jinja_env.get_template(self.name + '.jinja2')
            html_page = template.render({'pagetitle':self.pagetitle, 'name':'Joris'})
            #self.debug("handling"+str(msg), 'msg')
            #self.debug("Reply to " + str(msg['src']) + " / lcid=" + str(msg['lcid']), 'msg')
            rep = {'flags':'', 'prx_dst':msg['prx_src'], 'lcid':msg['lcid'], 'reply':html_page}
            self.debug("Reply = " + str(rep), 'msg')
            #self.debug("Queue = " + str(msg['src'].input))
            await self.msg_send(msg['prx_src'], rep)
            self.debug("Replied")
        else:
            await super().query_handle(msg)

