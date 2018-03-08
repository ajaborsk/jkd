import asyncio
import time
import datetime
import math

from .node import Node

class SerialLineProcess(Node):
    tagname = "serial_line_process"
    def __init__(self, elt = None, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = True)
        self.task_add('process', coro = self.parse, gets=['input'], returns=['output'])

        self.alpha_bat = 1.5961 # 4.065 * 10944 / 27872
        self.alpha_cir = 1.5888 # 4.065 * 10944 / 28000

        self.v_bat_old = None
        self.i_bat_old = None

        self.r_int_sum = 0
        self.r_int_sum_w = 0

    async def parse(self, line):
        self.debug('line to process: '+str(line))
        if len(line) > 10 and line[0:6] == 'OK 20 ':
            lst = line[6:].strip(' \r\n').split(' ')
            data = list(map(lambda a:a[0]+256*a[1], zip([int(k) for k in lst[::2]], [int(k) for k in lst[1::2]])))

            self.debug(str(data))
            v_bat = self.alpha_bat / data[1] * data[3]
            if self.v_bat_old is not None:
                delta_v_bat = v_bat - self.v_bat_old
            else:
                delta_v_bat = None
            self.v_bat_old = v_bat
            v_cir = self.alpha_cir / data[1] * data[4]
            i_bat = -(v_cir - v_bat) / 0.1 * 1000 # milli amps
            if self.i_bat_old is not None:
                delta_i_bat = i_bat - self.i_bat_old
            else:
                delta_i_bat = None
            self.i_bat_old = i_bat

            if delta_v_bat is not None and delta_i_bat is not None and math.fabs(delta_i_bat) > 5.:
                r_int_bat = -delta_v_bat / delta_i_bat * 1000
                r_int_w = math.fabs(delta_i_bat / 10.)
            else:
                r_int_bat = -1.
                r_int_w = 0.

            if r_int_bat > 0.:
                self.r_int_sum += r_int_bat * r_int_w
                self.r_int_sum_w += r_int_w

            if self.r_int_sum_w > 2.:
                r_int_mean = self.r_int_sum / self.r_int_sum_w
            else:
                r_int_mean = -1

            if r_int_mean > 0:
                v_bat_e = v_bat + r_int_mean * i_bat / 1000.
            else:
                v_bat_e = v_bat

            return "{}:{:5d} - [{:5d}] Vbat:{:6.4f}V  Vcir:{:6.4f}V  Ibat:{:5.0f}mA Pbat:{:5.0f}mW Rbat:{:4.2f}Ohm Rbat_e:{:4.2f}Ohm Vbat_e:{:5.3f}V".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()), data[0], data[1], v_bat, v_cir, i_bat, v_bat * i_bat, r_int_bat, r_int_mean, v_bat_e)
        else:
            return "Badly formated line"
            # value = 12.9
            # #self.debug('value: '+str(value))
            # return 'processed: '+line

