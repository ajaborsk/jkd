
from bokeh.plotting import figure
from bokeh.models import Range1d
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource

from .node import *

class BokehOfflineReportHtml(Node):
    """A dynamic offline html report

       Inputs : (#TODO)
         - data (DataTable)
         - configuration
       Outputs :
         - a html dynamic report (as a utf8 string)
       Configuration (#TODO) :
         - page title
         - columns
         - figure type
         - default zoom
         - color(s)
         - alpha
    """

    def __init__(self, content = None, **kwargs):
        super().__init__(**kwargs)
        self.cds = ColumnDataSource(data = {
                'x1':[0, 1, 2, 3, 4, 5, 6, 7,  8,  9, 10, 9],
                'y1':[0, 8, 2, 4, 6, 9, 5, 6, 25, 28,  4, 7]
                })
        self.TOOLS="pan,wheel_zoom,box_zoom,reset,save"
        # data range
        self.xr1 = Range1d(start=0, end=15)
        self.yr1 = Range1d(start=0, end=30)
        # build our figures
        self.p1 = figure(x_range=self.xr1, y_range=self.yr1, tools=self.TOOLS, plot_width=900, plot_height=600)
        self.p1.scatter('x1', 'y1', size=12, color="blue", alpha=0.5, source = self.cds)

    async def aget(self, portname = None):
        return file_html(self.p1, CDN, "The title")

