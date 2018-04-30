import asyncio
import time
import datetime
import math
import pandas as pd
import numpy as np

from .data_process import DataProcess

class Multipivot(DataProcess):
    tagname = "multipivot"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('control', mode = 'input')
        self.port_add('output0', cached = True, timestamped = False)
        self.port_add('output1', cached = True, timestamped = False)
        self.task_add('mp_loop', coro = self.mp_loop, needs=['input'], provides=['output0', 'output1'])

    async def mp_loop(self, args={}):
        data = await self.port_input_get("input", args)

        dftest = pd.DataFrame([[1.,2.],[3.,5.]], columns=['c1','c2'])
        dftest2 = pd.DataFrame([[1.5,2.5],[3.3,5.1]], columns=['c3','c4'])

        await self.port_value_update("output0", dftest)
        output = pd.pivot_table(data, values=["Prix"], index=['Age'], columns=['DOMAINE'], fill_value = 0, aggfunc=np.sum)['Prix']
        output['Age'] = output.index
        await self.port_value_update("output1", output)

        ports_list = ['input', 'control']
        while True:
            wait_list = []
            for portname in ports_list:
                if 'queue' in self.ports[portname]:
                    wait_list.append(self._wait_for_port(portname))
            self.debug("-*-*- Entering ")
            done, pending = await asyncio.wait(wait_list, return_when = asyncio.FIRST_COMPLETED)
            for p in pending:
                p.cancel()
            for d in done:
                r = d.result()
                self.debug("T: "+str(r[0])+' '+str(r[1]))
            self.debug("-*-*- Exited ")
            dftest['c1'] = dftest['c2'] + dftest['c1']
            dftest2['c4'] = dftest2['c3'] + dftest2['c4']
            await self.port_value_update("output0", dftest)
            output = pd.pivot_table(data, values=["Prix"], index=['Age'], columns=['DOMAINE'], fill_value = 0, aggfunc=np.sum, margins=True)['Prix']
            output['Age'] = output.index
            await self.port_value_update("output1", output)
#            await asyncio.sleep(16.)
