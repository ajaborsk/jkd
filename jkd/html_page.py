#from jinja2 import Environment, PackageLoader, select_autoescape

import jinja2

from .node import *

class HtmlPart:
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None):
        self.scripts = []
        self.css = []
        self.html = ""
        self.js = ""


class HtmlPartTable(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None):
        pass


class HtmlPartChart(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None):
        pass


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
        defs = [] # already defined id's
        for part_node in elt:
            self.debug("  Page part: {}".format(part_node.tag))
            part = dict(part_node.attrib)
            part['jkd_class'] = str(part_node.tag)
            if "id" not in part:
                n = 1
                while str(part_node.tag) + '_' + str(n) in defs:
                    n += 1
                part["id"] = str(part_node.tag) + '_' + str(n)
            defs.append(part["id"])
            if "class" not in part:
                part["class"] = str(part_node.tag)
            self.parts.append(part)
            #self.parts.append({'template':self.jinja_env.get_template(part.attrib['template'] + '.jinja2')})

    async def generate(self, args={}):
        scripts = []
        css = []
        html = []
        js = []
        for part in self.parts:
            pass
        template = self.jinja_env.get_template(self.name + '.jinja2')
        html_page = template.render({'pagetitle':self.pagetitle, 'name':'Joris', 'parts':self.parts})
        return html_page


