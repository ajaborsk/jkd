import io
import asyncio
import time
import datetime
import math
import json
import struct

from .node import Node

class HistoryInfluxDB(Node):
    """A simple history class. Uses InfluxDB to store/retrieve histories.
    """
    tagname = "history_influxdb"
    ##TODO
    def __init__(self, elt = None, timestamp = False, **kwargs):
        super().__init__(elt=elt, **kwargs)
        self.idx_rec_size = struct.calcsize('<QQL')
        self.timestamp = timestamp
        self.update_queue = None
        self.port_add('input', mode = 'input')
        self.port_add('output', cached = True, timestamped = False)
        self.task_add('process', autolaunch = True, coro = self.historize, needs=['input'], provides=[])
        #self.task_add('history', coro = self.history, gets=[], returns=['output'])
        self.task_add('history2', coro = self.history2, needs=[], provides=['output'])

    async def historize(self):
        self.ports['input']['queue'] = asyncio.Queue(maxsize=5)
        fqn = self.fqn().split('/')[1:]
        self.filename = fqn[0] + '/var/' + '.'.join(fqn)
        self.debug('history filename: '+str(self.filename+'.data'))
        self.data_file = open(self.filename+'.data', mode='ab', buffering = 0)
        self.current_pos = self.data_file.tell()
        self.debug('current pos: '+str(self.current_pos))
        self.debug('index filename: '+str(self.filename+'.idx'))
        self.index_file = open(self.filename+'.idx', mode='ab', buffering = 0)
        while True:
            data = await self.port_read('input')
            if self.timestamp:
                data = [time.time(), data]
            if data[1] is not None:
                self.debug('data: '+str(data))
                data_bin = json.dumps(data).encode('utf8')
                #self.debug('1: '+str(data))
                pos = self.current_pos
                self.data_file.write(data_bin)
                #self.debug('2: '+str(data))
                self.current_pos = self.data_file.tell()
                size = self.current_pos - pos
                index_bin = struct.pack('<QQL', int(data[0]), pos, size)
                #self.debug('3: '+str(data))
                self.index_file.write(index_bin)
                #self.debug('4: '+str(data))
                if self.update_queue is not None:
                    self.update_queue.put_nowait(0)

    def index_get_ts(self, indexf, cur_idx):
        #self.debug('idx: '+str(cur_idx))
        indexf.seek(cur_idx * self.idx_rec_size)
        idx_b = indexf.read(self.idx_rec_size)
        idx = struct.unpack('<QQL', idx_b)
        #self.debug('idx: '+str(cur_idx)+' ts: '+str(idx[0]))
        return idx[0]

    def index_before(self, ts):
        "Returns index in data file for last record that is before (or at) timestamp ts"
        #self.debug('target ts: '+str(ts))
        index_file = open(self.filename+'.idx', mode='rb')
        start_idx = 0
        start_ts = self.index_get_ts(index_file, start_idx)
        end_idx = int(index_file.seek(0, io.SEEK_END) // self.idx_rec_size) - 1
        end_ts = self.index_get_ts(index_file, end_idx)
        if end_ts <= ts:
            index_file.close()
            return end_idx
        if start_ts > ts:
            index_file.close()
            return None
        # Start dichotomy algorithm
        while end_idx - start_idx > 1:
            cur_idx = int((start_idx + end_idx) // 2)
            cur_ts = self.index_get_ts(index_file, cur_idx)
            if cur_ts <= ts:
                start_idx = cur_idx
                start_ts = cur_ts
            else:
                end_idx = cur_idx
                end_ts = cur_ts
        index_file.close()
        return cur_idx

    def index_after(self, ts):
        "Returns index in data file for first record that is after (or at) timestamp ts"
        #self.debug('target ts: '+str(ts))
        index_file = open(self.filename+'.idx', mode='rb')
        start_idx = 0
        start_ts = self.index_get_ts(index_file, start_idx)
        end_idx = int(index_file.seek(0, io.SEEK_END) // self.idx_rec_size) - 1
        end_ts = self.index_get_ts(index_file, end_idx)
        if end_ts <= ts:
            index_file.close()
            return None
        if start_ts > ts:
            index_file.close()
            return start_idx
        # Start dichotomy algorithm
        while end_idx - start_idx > 1:
            cur_idx = int((start_idx + end_idx) // 2)
            cur_ts = self.index_get_ts(index_file, cur_idx)
            if cur_ts < ts:
                start_idx = cur_idx
                start_ts = cur_ts
            else:
                end_idx = cur_idx
                end_ts = cur_ts
        index_file.close()
        return cur_idx

    async def history(self, args = {}):
        result = []
        data_file = open(self.filename+'.data', mode='rb')
        index_file = open(self.filename+'.idx', mode='rb')
        done = False
        before_ts = float(args.get("before", math.inf))
        after_ts = float(args.get("after", -math.inf))

        index_after = self.index_after(after_ts)
        if index_after is None:
            yield []
            return
#            return []
        else:
            index_file.seek(index_after * self.idx_rec_size)

        count = 0
        while not done:
            idx_b = index_file.read(self.idx_rec_size)
            if len(idx_b) == self.idx_rec_size:
                idx = struct.unpack('<QQL', idx_b)
                #self.debug(str(idx))
                if idx[0] < before_ts:
                    data_file.seek(idx[1])
                    b_data = data_file.read(idx[2])
                    #self.debug(' '+repr(idx)+' '+repr(b_data))
                    data = json.loads(b_data.decode('utf-8'))
                    result.append(data)
                    count += 1
                    if count % 10000:
                        #yield []
                        pass
                else:
                    done = True
            else:
                done = True
        data_file.close()
        index_file.close()
        yield result
        return
        #return result

    async def history2(self, args = {}):
        self.update_queue = asyncio.Queue()
        while True:
            result = []
            data_file = open(self.filename+'.data', mode='rb')
            index_file = open(self.filename+'.idx', mode='rb')
            done = False
            before_ts = float(args.get("before", math.inf))
            after_ts = float(args.get("after", -math.inf))

            if after_ts < 0:
                after_ts = time.time() + after_ts

            index_after = self.index_after(after_ts)
            if index_after is None:
                done = True
            else:
                index_file.seek(index_after * self.idx_rec_size)

            count = 0
            while not done:
                idx_b = index_file.read(self.idx_rec_size)
                if len(idx_b) == self.idx_rec_size:
                    idx = struct.unpack('<QQL', idx_b)
                    #self.debug(str(idx))
                    if idx[0] < before_ts:
                        data_file.seek(idx[1])
                        b_data = data_file.read(idx[2])
                        #self.debug(' '+repr(idx)+' '+repr(b_data))
                        data = json.loads(b_data.decode('utf-8'))
                        result.append(data)
                        count += 1
                        if count % 10000:
                            #yield []
                            pass
                    else:
                        done = True
                else:
                    done = True
            data_file.close()
            index_file.close()
            # if len(result) >= 1:
                # self.debug("########## last:" + repr(result[-1]))
            await self.port_value_update('output', result)

            # Wait for new input but don't use returned value
            dummy = await self.update_queue.get()
            # consume all queue
            while not self.update_queue.empty():
                dummy = await self.update_queue.get()
