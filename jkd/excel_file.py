import itertools

import pandas as pd
import openpyxl

from .data_file import DataFile

class ExcelFile(DataFile):
    tagname = "excel_file"
    def __init__(self, file="", elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)

        #self.data = None
        fqn = self.fqn().split('/')[1:]
        self.filename = fqn[0] + '/var/' + file

        #self.port_add('output', cached = False, timestamped = True)

        self.sheets = []
        output_port_names = []
        for el in elt:
            if el.tag == "sheet":
                self.sheets.append(dict(el.attrib))
                self.port_add(el.get("port", "sheet"), timestamped=False)
                output_port_names.append(el.get("port", "sheet"))

        self.task_add('process', coro = self.process, gets=[], returns=list(output_port_names))

    async def process(self, args={}):
        wb = openpyxl.load_workbook(self.filename)
        data = []
        for sheet in self.sheets:
            data_sheet = wb[sheet['name']]
            sheet_data = data_sheet.values
            cols = next(sheet_data)[:]
            sheet_data = list(sheet_data)
            #idx = ["{:04d}-{:05d}".format(r[0], r[1]) for r in sheet_data]
            #uidx = ["{:04d}".format(r[2]) for r in sheet_data]
            sheet_data = (itertools.islice(r, 0, None) for r in sheet_data)
            #df = pd.DataFrame(sheet_data, index=pd.MultiIndex.from_arrays([idx, uidx]), columns=cols)
            df = pd.DataFrame(sheet_data, columns=cols)
            data.append(df)
        if len(data) == 1:
            data = data[0]
        #data = pd.DataFrame([[j+i*0.01 for j in range(10)] for i in range(10)])
        return data
        #return (0, {'ports':self.ports, 'sheets': self.sheets, 'data':data.iloc[:100]})

