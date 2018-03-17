#from jinja2 import Environment, PackageLoader, select_autoescape

import jinja2

from .node import *

class HtmlPart:
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, **kwargs):
        self.p_class = p_class
        self.p_name = p_name
        self.p_id = p_id
        self.scripts = []
        self.css = []
        self.html_template = jinja2.Template("")
        self.js_template = jinja2.Template("")
        self.kwargs = kwargs

    def script_add(self, script_name):
        if script_name not in self.scripts:
            self.scripts.append(script_name)

    def css_add(self, css_name):
        if css_name not in self.css:
            self.css.append(css_name)

    def context(self):
        return {'p_id':self.p_id, 'p_class':self.p_class, 'p_name':self.p_name}

    def get_html(self):
        return self.html_template.render(self.context())

    def get_js(self):
        return self.js_template.render(self.context())


class HtmlPartValue(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, **kwargs):
        super().__init__(elt, p_class, p_name, p_id, **kwargs)


class HtmlPartTable(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, **kwargs):
        super().__init__(elt, p_class, p_name, p_id, **kwargs)


class HtmlPartChart(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, **kwargs):
        super().__init__(elt, p_class, p_name, p_id, **kwargs)


class HtmlPartEntry(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, data=None, **kwargs):
        super().__init__(elt, p_class, p_name, p_id, **kwargs)
        #parms = {'p_id':self.p_id}
        self.data_addr = data
        self.css_add("jkd.css")
        self.script_add("jkd.js")
        self.script_add("jkd-entry.js")
        self.html_template = jinja2.Template("""
  <!-- HtmlPartEntry {{p_id}} -->
  <div id="{{p_id}}-container">
    <input style="bgcolor:white;" id="{{p_id}}-input">Data</input>
    <div style="">
      <span id="{{p_id}}-send" style="text-align:center; display:inline-block; width:12%; height:30px;">Send</span>
      <span id="{{p_id}}-enter" style="text-align:center; display:inline-block; width:12%; height:30px;">Enter</span>
      <span id="{{p_id}}-leave" style="text-align:center; display:inline-block; width:12%; height:30px;">Leave</span>
    </div>
  </div>
  <!-- HtmlPartEntry end -->""")
        self.js_template = jinja2.Template("""
  // HtmlPartHisto {{p_id}} script part

  var hc = new JkdHistoryChart(jkd_env, "{{p_id}}", "{{data_addr}}");

  // end of HtmlPartHisto script part
""")

class HtmlPartHisto(HtmlPart):
    def __init__(self, elt = None, p_class = None, p_name = None, p_id = None, data=None, **kwargs):
        super().__init__(elt, p_class, p_name, p_id, **kwargs)
        #parms = {'p_id':self.p_id}
        self.data_addr = data
        self.css_add("jkd.css")
        self.script_add("jkd.js")
        self.script_add("moment-with-locales.min.js")
        self.script_add("Chart.bundle.min.js")
        self.script_add("hammer.min.js")
        self.script_add("chartjs-plugin-zoom.min.js")
        self.script_add("jkd-chart.js")
        self.html_template = jinja2.Template("""
  <!-- HtmlPartHisto {{p_id}} -->
  <div id="{{p_id}}-container">
    <canvas style="bgcolor:white;" id="{{p_id}}-canvas" width="800" height="200"></canvas>
    <div style="">
      <span id="{{p_id}}-update" style="text-align:center; display:inline-block; width:12%; height:30px;">Update</span>
      <span id="{{p_id}}-prev2" style="text-align:center; display:inline-block; width:12%; height:30px;">&lt;&lt;</span>
      <span id="{{p_id}}-prev" style="text-align:center; display:inline-block; width:12%; height:30px;">&lt;</span>
      <span id="{{p_id}}-duration" style="text-align:center; display:inline-block; width:12%; height:30px;">&lt;</span>
      <span id="{{p_id}}-next" style="text-align:center; display:inline-block; width:12%; height:30px;">&gt;</span>
      <span id="{{p_id}}-next2" style="text-align:center; display:inline-block; width:12%; height:30px;">&gt;&gt;</span>
      <span id="{{p_id}}-zoom" style="text-align:center; display:inline-block; width:12%; height:30px;">+</span>
      <span id="{{p_id}}-unzoom" style="text-align:center; display:inline-block; width:12%; height:30px;">-</span>
      <span id="{{p_id}}-zreset" style="text-align:center; display:inline-block; width:12%; height:30px;">RAZ</span>
    </div>
  </div>
  <!-- HtmlPartHisto end -->""")
        self.js_template = jinja2.Template("""
  // HtmlPartHisto {{p_id}} script part

  var hc = new JkdHistoryChart(jkd_env, "{{p_id}}", "{{data_addr}}");

  // end of HtmlPartHisto script part
""")

    def context(self):
        ctx = super().context()
        ctx.update({'data_addr':self.data_addr})
        return ctx


class HtmlPage(Node):
    tagname = "html_page"
    def __init__(self, elt = None, parent = None, **kwargs):
        self.parts_registry = {'histo':HtmlPartHisto,
                               'value':HtmlPartValue,
                               'table':HtmlPartTable,
                               'entry':HtmlPartEntry,
                               'chart':HtmlPartChart}
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
            part = self.parts_registry[part_node.tag](**part_node.attrib)
            #part['jkd_class'] = str(part_node.tag)
            if part.p_id is None:
                n = 1
                while str(part_node.tag) + '_' + str(n) in defs:
                    n += 1
                part.p_id = str(part_node.tag) + '_' + str(n)
            defs.append(part.p_id)
            if part.p_class is None:
                part.p_class = str(part_node.tag)
            self.parts.append(part)
            #self.parts.append({'template':self.jinja_env.get_template(part.attrib['template'] + '.jinja2')})

    async def generate(self, args={}):
        scripts = ['jquery-3.3.1.min.js']
        css_list = []
        html = ""
        js = ""
        for part in self.parts:
            for script in part.scripts:
                if script not in scripts:
                    scripts.append(script)
            for css in part.css:
                if css not in css_list:
                    css_list.append(css)
            html += part.get_html()
            js += part.get_js()
        template = self.jinja_env.get_template(self.name + '.jinja2')
        html_page = template.render({'pagetitle':self.pagetitle, 'name':'Joris', 'css_list':css_list, 'scripts':scripts, 'js':js, 'html':html})
        return html_page
