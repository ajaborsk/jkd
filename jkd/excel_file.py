import pandas as pd
import openpyxl

from .data_file import DataFile

class ExcelFile(DataFile):
    tagname = "excel_file"
    def __init__(self, file="", elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)

        self.data = None
        self.filename = file

        #self.port_add('output', cached = False, timestamped = True)

        self.sheets = []
        for el in elt:
            if el.tag == "sheet":
                self.sheets.append(dict(el.attrib))
                self.port_add(el.get("port", "sheet"))

        self.task_add('process', coro = self.process, gets=[], returns=list(self.ports.keys()))

    async def process(self, args={}):
        data = pd.DataFrame([[j+i*0.01 for j in range(10)] for i in range(10)])
        return (0, data.iloc[:100])

