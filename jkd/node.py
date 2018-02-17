from urllib.parse import urlparse
import inspect
import asyncio

import xml.etree.ElementTree as ET

class Port:
    def __init__(self):
        self.input = asyncio.Queue()
        # Unused
        #self.output = asyncio.Queue()

    # Low level API (but maybe using directly Queue API would be sufficent ?)
    async def send(self, message):
        await self.input.put(message)

    async def recv(self):
        return await self.output.get()

    # High level API
    async def get(self, address = None):
        #TODO
        pass

    async def set(self, value, address = None):
        #TODO
        pass

    # conditional / complex get
    async def request(self, query, address = None):
        #TODO
        pass


class Node:
    def __init__(self, env = None, parent = None, name = ''):
        #print("setting env to", env)
        self.env = env
        self.parent = parent
        self.name = name
        self.debug(str(self.__class__) + " fqn: " + self.fqn())

        self.next_qid = 0
        # Global input messages queue
        self.input = asyncio.Queue()
        # I/O ports. each port has a entry in the dictionary : 'portname':{properties}
        self.ports = {}
        # Per-Query channels
        self.channels = {}
        self.done = False
        if self.env is not None and hasattr(self.env, 'loop'):
            #self.debug("launching mainloop...")
            self.loop_task = self.env.loop.create_task(self.mainloop())

    #TODO:  An API to add/remove/configure ports

    def fqn(self):
        if self.parent is None:
            return(self.name)
        else:
            return self.parent.fqn() + '/' + self.name

    async def mainloop(self):
        #self.debug(str(self.__class__)+self.name + ": Entering mainloop...")
        while not self.done:
            msg = await self.input.get()
            #self.debug(str(self.__class__) + self.name + ": Handling msg: " + str(msg))
            await self.msg_handle(msg)

    async def msg_handle(self, msg):
        # General message handling (including routing)
        #self.debug(self.name + ' msg_handle '+str(msg))
        if 'query' in msg:
            # This is a query
            if 'path' in msg and msg['path'] == self.name:
                # The node is the final destination
                await self.query_handle(msg)
            else:
                # Route to next node
                name_len = len(self.name)
                self.warning(self.name + ' : ' + str(name_len) + ' => '+ str(msg['path'][0:name_len + 2]))
                if msg['path'][0:name_len + 1] == self.name + '/':
                    msg['path'] = msg['path'][name_len + 1:]
                if msg['path'][0:name_len + 2] == '/' + self.name + '/':
                    msg['path'] = msg['path'][name_len + 2:]
                elt = msg['path'].split('/')[0]
                if elt in self:
                    await self.delegate(self[elt], msg)
                else:
                    self.warning('No route for '+str(msg))
        elif 'reply' in msg:
            # This is a reply
            #self.debug(self.name + ' reply catched : ' + str(msg))
            qid = msg['qid']
            if qid in self.channels:
                if isinstance(self.channels[qid], asyncio.Queue):
                    self.debug(self.name + ' reply queue mode : ' + str(msg))
                    # The node is the final destination (queue mode)
                    await self.channels[qid].put(msg)
                elif isinstance(self.channels[qid], tuple):
                    #self.debug(self.name + ' reply coro mode : ' + str(msg))
                    # The node is the final destination (coroutine mode)
                    await self.channels[qid][0](msg, self.channels[qid][1])
                else:
                    # Just route to next node
                    self.debug(self.name + ' reply reroute mode : ' + str(msg))
                    msg['qid'] = self.channels[qid]['qid']
                    msg['prx_src'] = self
                    self.channels[qid]['prx_dst'].input.put(msg)
                if 'eoq' in msg and msg['eoq'] == True:
                    # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    del self.channels[qid]
        elif 'error' in msg:
            # This is a (replied) error
            if 0:
                # The node is the final destination
                pass
            else:
                # Just route to next node
                pass
        elif 'node' in msg and msg['node'] == self.name:
            # This node is the final destination
            # TODO
            pass
        elif 'query' not in msg:
            # This is a reply
            qid = msg['qid']
            if qid in self.channels:
                await self.channels[qid].put(msg)
                if 'eoq' in msg and msg['eoq'] == True:
                    # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    del self.channels[qid]
            else:
                self.warning('No registred query id '+str(qid))
        else:
            self.warning(str(self.__class__) + self.name + ": Unhandled msg: " + str(msg))

    def get_etnode(self):
        return ET.Element()

    # Outgoing query
    async def query(self, destination, query, coro = None, client = None):
        # get next query id (qid) and increment counter for next time
        qid = self.next_qid
        self.next_qid += 1
        if 'url' in query:
            if coro is None:
                self.channels[qid] = asyncio.Queue()
            else:
                self.channels[qid] = (coro, client)
            url = urlparse(query['url'])
            self.debug(self.name+': '+"Url = "+str(url))
            query.update({'path':url.path, 'port':url.fragment, 'qid':qid, 'prx_src':self})
            await destination.input.put(query)
            return qid
        elif 'node' in query:
            # New protocol
            if 'prox_src' in query:
                prox_dst = query['prox_src']
            else:
                prox_dst = query['src']
            self.current_queries[qid] = {'qid': query['qid'], 'prox_dst': prox_dst}
            query.update({'qid':qid, 'prox_src':self})
            await destination.input.put(query)
        else:
            # Add a internal dedicated queue for this query id
            self.channels[qid] = asyncio.Queue()
            # Update message with qid and source reference (as python object for now)
            query.update({'qid':qid, 'src':self})
            # Put the message into the destination (global) queue
            await destination.input.put(query)
            # Return the query id
            return qid

    async def delegate(self, destination, query):
        self.debug("Delegating to " + str(destination)+' : '+str(query))
        query['path'] = destination.name
        await destination.input.put(query)

    async def wait_for_reply(self, qid, timeout = 10.):
        return await asyncio.wait_for(self.channels[qid].get(), timeout, loop = self.env.loop)

    async def query_handle(self, query):
        # called when the node is the final destination of the query
        #TODO : port management ??
        self.debug(self.name + ": generic query handle" + str(query))
        if 'port' in query and query['port'] in self.ports:
            port = query['port']
            self.debug(self.name + ": port = " + str(query))
            if query['query'] == 'immediate':
                reply = {'qid':query['qid'], 'reply':self.ports[port]['value']}
                self.debug(self.name + ": immediate reply = " + str(query) + ' ' + str(reply))
                await query['prx_src'].input.put(reply)
            else:
                # Subscription
                self.debug(self.name + ": subscribtion => " + str(query))
                self.ports[port]['connections'].append({'update':True, 'qid':query['qid'], 'prx_dst':query['prx_src']})
                self.debug(self.name + ": subscribtions = " + str(self.ports[port]['connections']))

    async def reply_handle(self, reply):
        # called when the node is the final destination of the reply
        pass

    async def aget(self, portname = None):
        """Return a ElementTree that represent the Node full state (if possible) or the port value
        """
        self.warning("Unimplemented aget() method.")

    def serialize(self):
        """
        """
        pass

    def connect(self, dest, **kwargs):
        #TODO: whole thing...
        pass

    def debug(self, *args, logger='main'):
        self.env.loggers[logger].debug(*args)

    def info(self, *args, logger='main'):
        self.env.loggers[logger].info(*args)

    def warning(self, *args, logger='main'):
        self.env.loggers[logger].warning(*args)

    def error(self, *args, logger='main'):
        self.env.loggers[logger].error(*args)
