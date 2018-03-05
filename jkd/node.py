from urllib.parse import urlparse
import inspect
import asyncio
import logging
import time


import xml.etree.ElementTree as ET

# class Port:
    # def __init__(self):
        # self.input = asyncio.Queue()
        # # Unused
        # #self.output = asyncio.Queue()

    # # Low level API (but maybe using directly Queue API would be sufficent ?)
    # async def send(self, message):
        # await self.input.put(message)

    # async def recv(self):
        # return await self.output.get()

    # # High level API
    # async def get(self, address = None):
        # #TODO
        # pass

    # async def set(self, value, address = None):
        # #TODO
        # pass

    # # conditional / complex get
    # async def request(self, query, address = None):
        # #TODO
        # pass


class Node:
    tagname = "node"
    def __init__(self, env = None, parent = None, name = ''):
        #print("setting env to", env)
        self.env = env
        self.parent = parent
        self.name = name
        self.debug(str(self.__class__) + " fqn: " + self.fqn())

        # Next available Local Channel ID (lcid)
        self.next_lcid = 0
        # Global input messages queue
        self.input = asyncio.Queue()
        # I/O ports. each port has a entry in the dictionary : 'portname':{properties}
        self.ports = {}
        self.tasks = {}
        self.methods = {'get':self.method_get}

        # Per-Query channels
        # channels segments which this node created
        # key = lcid of previous/current channel segment (from node source to this one)
        # 'lcid': local channel id (from this node toward destination). Assigned by next node in the channel.
        # 'prx_dst' : python node messages have to be sent (next node)
        self.channels = {}

        # channels segments which this node is destination (build on replies)
        # key = (prx_dst_id, lcid) : python id of the next node, lcid ofthe next segment
        # 'lcid' : lcid assigned by this node to the previous channel segment
        # 'prx_src' : python node messages come from (or back messages have to be sent)
        self.back_channels = {}

        self.done = False

        self.port_add('state')
#        if self.env is not None and hasattr(self.env, 'loop'):
#            #self.debug("launching msg_queue_loop()...")
#            self.loop_task = self.env.loop.create_task(self.msg_queue_loop())

        self.task_add('_msg_loop', coro = self.msg_queue_loop, autolaunch = True)
        self.task_add('_state', coro = self._introspect, returns = ['state'])


    def task_add(self, taskname, coro = None, gets = [], returns = [], needs = [], provides = [], autolaunch = False):
        """Add a task to node tasks list
        """
        self.tasks[taskname] = {'coro':coro,
                                'gets':gets,
                                'returns':returns,
                                'needs':needs,
                                'provides':provides,
                                'autolaunch':autolaunch,
                                'task':None }

    def port_add(self, portname, mode = 'output', cached = False, timestamped = False):
        self.ports[portname] = { 'mode': mode,
                                 'cached': cached,
                                 'timestamped': timestamped,
                                 'connections':[]}

    async def port_read(self, portname):
        #TODO
        pass

    async def port_value_update(self, portname, value):
        #self.debug('portname: '+str(portname))
        port = self.ports[portname]
        #self.debug('port: '+str(port))
        if port.get('cached', False):
            port['value'] = value
        for cnx in port['connections']:
            #self.debug('cnx: '+str(cnx))
            if 'update' in cnx:
                if 'finished' not in cnx or cnx['finished'] == False:
                    flags = 'f'
                    cnx['finished'] = True # Channel *opening* is finished
                else:
                    flags = ''
                if port.get('timestamped', False):
                    msg = {'prx_src':self, 'lcid':cnx['lcid'], 'flags':flags, 'reply':(time.time(), value)}
                else:
                    msg = {'prx_src':self, 'lcid':cnx['lcid'], 'flags':flags, 'reply':value}
                #self.debug(str(self.name) + " : output_msg to "+str(cnx['prx_dst'])+': '+str(msg))
                await self.msg_send(cnx['prx_dst'], msg)

    def run(self):
        # Prepare : make link between ports and tasks
        for taskname in self.tasks:
            for portname in self.tasks[taskname]['returns']:
                if portname in self.ports:
                    if 'returned_by' in self.ports[portname]:
                        self.warning('port "{}" value returned by "{}" is already returned by task "{}"'.format(portname, taskname, self.ports[portname]['returned_by']))
                    elif 'provided_by' in self.ports[portname]:
                        self.warning('port "{}" value returned by "{}" is already provided by task "{}"'.format(portname, taskname, self.ports[portname]['provided_by']))
                    else:
                        self.ports[portname]['returned_by'] = taskname
                else:
                    self.warning('task "{}" returns unkown port "{}"'.format(taskname, portname))
            for portname in self.tasks[taskname]['provides']:
                if portname in self.ports:
                    if 'returned_by' in self.ports[portname]:
                        self.warning('port "{}" value provided by "{}" is already returned by task "{}"'.format(portname, taskname, self.ports[portname]['returned_by']))
                    elif 'provided_by' in self.ports[portname]:
                        self.warning('port "{}" value provided by "{}" is already provided by task "{}"'.format(portname, taskname, self.ports[portname]['provided_by']))
                    else:
                        self.ports[portname]['provided_by'] = taskname
                else:
                    self.warning('task "{}" provides unkown port "{}"'.format(taskname, portname))
            for portname in self.tasks[taskname]['gets']:
                if portname in self.ports:
                    self.ports[portname]['got_by'] = taskname
                else:
                    self.warning('task "{}" gets unkown port "{}"'.format(taskname, portname))
            for portname in self.tasks[taskname]['needs']:
                if portname in self.ports:
                    self.ports[portname]['needed_by'] = taskname
                else:
                    self.warning('task "{}" needs unkown port "{}"'.format(taskname, portname))

        # Launch autolaunch tasks
        if self.env is not None and hasattr(self.env, 'loop'):
            for taskname in self.tasks:
                if self.tasks[taskname].get('autolaunch'):
                    self.debug("(auto)launching task: " + taskname)
                    self.tasks[taskname]['task'] = self.env.loop.create_task(self.tasks[taskname]['coro']())

    #TODO:  An API to add/remove/configure ports

    def fqn(self):
        "Fully Qualified Name"
        if self.parent is None:
            return(self.name)
        else:
            return self.parent.fqn() + '/' + self.name

    async def method_get(self, msg):
        self.debug("msg: "+str(msg), 'msg')
        portname = msg['port']
        if portname not in self.ports:
            self.warning('Trying to get value of unknown port "{}"'.format(portname), 'msg')
            return None
        else:
            port = self.ports[portname]
        self.debug('policy ='+str(msg['policy'])+' port='+str(portname), 'msg')
        if msg['policy'] == 'immediate':
            # Check if a task provides the port value.
            if 'provided_by' in port:
                # Port is *provided* by a task
                #TODO
                self.warning("TODO")
            elif 'returned_by' in port:
                self.debug("returned_by mode: "+str(msg), 'msg')
                # Port is *returned* by a task
                if len(self.tasks[port['returned_by']]['returns']) == 1:
                    task = self.tasks[port['returned_by']]
                    # Get needed parameters for task
                    args = []
                    for gets in task['gets']:
                        self.warning("TODO")
                    # Launch task
                    self.debug("launch task: "+str(task)+' '+str(args), 'msg')
                    result = await task['coro'](*args)
                    self.debug("result: "+str(result), 'msg')
                    # Send reply
                    response = {'flags':'d', 'prx_src':self, 'lcid':msg['lcid'], 'reply':result}
                    #response = {'flags':'d', 'prx_src':self, 'prx_dst':msg['prx_src'], 'lcid':msg['lcid'], 'reply':result}
                    await self.msg_send(msg['prx_src'], response)
                    self.debug("Replied with:"+str(response), 'msg')
                else:
                    # task returns more than this port value
                    #TODO
                    self.warning("TODO")
            else:
                self.warning('port "{}" is not provided nor returned by any task.'.format(portname))
                return None
        elif msg['policy'] == 'on_update':
            if 'provided_by' in port:
                self.debug("provided_by mode: "+str(msg), 'msg')
                if len(self.tasks[port['provided_by']]['provides']) == 1:
                    task = self.tasks[port['provided_by']]
                    if task['task'] is None:
                        # The task isn't running => launch it
                        self.debug('Launching task: '+str(port['provided_by'])+' '+str(task['coro']))
                        task['task'] = self.env.loop.create_task(task['coro']())
                        self.debug('Launched task: '+str(port['provided_by']))
                # Add a subscription to the port
                cnx = {'update':True, 'lcid':msg['lcid'], 'prx_dst':msg['prx_src']}

                # Update back_channels
                key = (id(msg['prx_src']), msg['lcid'])
                self.debug("key= "+str(key), 'msg')
                self.back_channels[key] = {'port':msg['port'], 'cnx_idx':len(port['connections'])}
                self.debug("Updated back_channels " + str(key) + ' : ' +  str(self.back_channels[key]), 'msg')

                # Add connection to the port
                port['connections'].append(cnx)
                self.debug(self.name + ": subscriptions = " + str(port['connections']), 'msg')
        else:
            self.warning("Unhandled policy: "+str(msg['policy']))

    async def msg_queue_transmit(self, destination, msg, delegate = False):
        "Low level queue message API"
        self.debug("transmit to " + str(destination) + ': ' + str(msg), 'msg')
        if 'c' in msg['flags']:
            # Create a new outgoing channel
            msg['lcid'] = self.next_lcid
            self.next_lcid += 1
        else:
            pass
            # Use previously set lcid
            ##channel = self.back_channels[(id(msg['prx_src']), msg['lcid'])]
            ##msg.update({'prx_src':self, 'lcid':channel['lcid']})
        # Always set the proxy source (which is this node)
        msg['prx_src'] = self
        await destination.input.put(msg)
        self.debug("Transmitted.", 'msg')
        if 'cmd' in msg and 'd' in msg['flags']:
            # remove channel, only in "command" mode
            lcid = msg['lcid'] # only for debug purpose
            del self.channels[msg['lcid']]
            self.debug("removed channel lcid: "+str(lcid), 'msg')
            return None
        else:
            return msg['lcid']

    async def msg_queue_loop(self):
        #self.debug("Entering msg_queue_loop...")
        while not self.done:
            self.debug('Waiting for message...', 'msg')
            msg = await self.input.get()
            self.debug("Received msg: " + str(msg), 'msg')
            if 'c' in msg['flags']:
                # Simple route
                #TODO
                pass
            elif 'f' in msg['flags']:
                # Update back_channels
                lcid = msg['lcid']
                # test for "hashability"
                try:
                    hash(self.channels[lcid])
                    trace_it = True
                except TypeError:
                    trace_it = False
                if trace_it:
                    key = self.channels[lcid]
                    #self.debug("Updating back_channels " + str(key) + ' : ' +  str((lcid, msg['prx_src'])), 'msg')
                    self.back_channels[key] = {'lcid':lcid, 'prx_dst':msg['prx_src']}
                    self.debug("Updated back_channels " + str(key) + ' : ' +  str(self.back_channels[key]), 'msg')
#            await self.msg_queue_handle(msg)
            self.env.loop.create_task(self.msg_queue_handle(msg))

    async def msg_send(self, destination, message, delegate = False):
        "Low level message API"
        #message.update({'prx_src':self})
#        return await destination.input.put(message)
        # Default transmission mode is python queue
        return await self.msg_queue_transmit(destination, message, delegate = delegate)

    async def msg_queue_handle(self, msg):
        # General message (from input queue) handling (including routing)
        self.debug('(generic) queue msg handle: ' + str(msg), 'msg')
        if 'method' in msg:
            # This is a query
            if 'path' in msg and msg['path'] == self.name:
                self.debug('I am final dest for msg: ' + str(self.msg_query_handle), 'msg')
                # The node is the final destination
                await self.msg_query_handle(msg)
            else:
                # Route/delegate to next node
                name_len = len(self.name)
                self.debug(self.name + ' : ' + str(name_len) + ' => '+ str(msg['path'][0:name_len + 2]), 'msg')
                if msg['path'][0:name_len + 1] == self.name + '/':
                    msg['path'] = msg['path'][name_len + 1:]
                if msg['path'][0:name_len + 2] == '/' + self.name + '/':
                    msg['path'] = msg['path'][name_len + 2:]
                elt = msg['path'].split('/')[0]
                if elt in self:
                    await self.msg_reroute(self[elt], msg)
                else:
                    self.warning('No route for '+str(msg), 'msg')
        elif 'reply' in msg:
            # This is a reply
            self.debug(self.name + ' reply catched : ' + str(msg), 'msg')
            lcid = msg['lcid']
            if lcid in self.channels:
                if isinstance(self.channels[lcid], asyncio.Queue):
                    self.debug(self.name + ' reply queue mode : ' + str(msg), 'msg')
                    # The node is the final destination (queue mode)
                    await self.channels[lcid].put(msg)
                elif isinstance(self.channels[lcid], tuple):
                    #self.debug(self.name + ' reply coro mode : ' + str(msg), 'msg')
                    # The node is the final destination (coroutine mode)
                    await self.channels[lcid][0](msg, self.channels[lcid][1])
                else:
                    # Just route to next node
                    #self.debug(self.name + ' reply  mode : ' + str(msg), 'msg')
                    msg['lcid'] = self.channels[lcid]['lcid']
                    msg['prx_src'] = self
                    await self.msg_send(self.channels[lcid]['prx_dst'], msg)
                if 'eoq' in msg and msg['eoq'] == True:
                    # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    del self.channels[lcid]
        elif 'error' in msg:
            # This is a (replied) error
            if 0:
                # The node is the final destination
                pass
            else:
                # Just route to next node
                pass
        elif 'cmd' in msg:
            # This is a query update
            #self.debug("Query update: " + str(msg), "msg")
            key = (id(msg['prx_src']), msg['lcid'])
            #self.debug("Query update: key = " + str(key), 'msg')
            if key in self.back_channels:
                #self.debug("Query update: key = " + str(key) + "" + str(self.back_channels[key]), 'msg')
                if msg['cmd'] == 'close':
                    # Remove/close connexion
                    del self.ports[self.back_channels[key]['port']]['connections'][self.back_channels[key]['cnx_idx']]
                    #TODO: propagate channel closing !!
                else:
                    self.warning("Unhandled Query update (unknown command) : " + str(msg), 'msg')
            else:
                self.warning("Unhandled Query update (unknown channel) : " + str(msg), 'msg')
        # elif 'node' in msg and msg['node'] == self.name:
            # # This node is the final destination
            # # TODO
            # pass
        # elif 'query' not in msg:
            # # This is a reply
            # lcid = msg['lcid']
            # if lcid in self.channels:
                # await self.channels[lcid].put(msg)
                # if 'eoq' in msg and msg['eoq'] == True:
                    # # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    # del self.channels[lcid]
            # else:
                # self.warning('No registred query id '+str(lcid), 'msg')
        else:
            self.warning(str(self.__class__) + self.name + ": Unhandled msg: " + str(msg), 'msg')

    def get_etnode(self):
        return ET.Element()

    # Outgoing query
    async def msg_query(self, destination, query, coro = None, client = None, timeout = 0):
        if 'url' in query:
            url = urlparse(query['url'])
            #self.debug(self.name+': '+"Url = " + str(url), 'msg')
            if 'port' in query:
                # do not update 'port' if preexistent
                query.update({'path':url.path, 'flags':'c'})
            else:
                query.update({'path':url.path, 'port':url.fragment, 'flags':'c'})
        else:
            self.warning('No url for query' + str(query), 'msg')
        lcid = await self.msg_send(destination, query)
        if coro is None:
            # Add a internal dedicated queue for this channel id
            self.channels[lcid] = asyncio.Queue()
            self.debug('channels['+str(lcid)+'] = '+str(self.channels[lcid]), 'msg')
            if timeout != 0:
                response = None
                try:
                    self.debug("Waiting for reply...", 'msg')
                    msg = await self.msg_wait_for_reply(lcid, timeout = timeout)
                    self.debug("Reply received: "+str(msg['reply']), 'msg')
                    response = msg['reply']
                except asyncio.TimeoutError:
                    self.info("msg query timeout", 'msg')
                if lcid in self.channels:
                    del self.channels[lcid] # remove query input queue
                return response
        else:
            # Add a callback and its client data for this channel id
            self.channels[lcid] = (coro, client)
            self.debug('channels['+str(lcid)+'] = '+str(self.channels[lcid]), 'msg')
        return lcid

    async def msg_queue_delegate(self, destination, query):
        #self.debug("Delegating to " + str(destination)+' : '+str(query), 'msg')
        query['path'] = destination.name
#        await self.msg_send(destination, query, delegate = True)
        await destination.input.put(query)

    async def msg_reroute(self, destination, query):
        #self.debug("Rerouting to " + str(destination)+' : '+str(query), 'msg')
#        await self.msg_send(destination, query, delegate = True)
        await destination.input.put(query)

    async def msg_wait_for_reply(self, lcid, timeout = 10.):
        self.debug("Waiting for reply on channel "+str(lcid)+" queue: "+str(self.channels[lcid]), 'msg')
        return await asyncio.wait_for(self.channels[lcid].get(), timeout, loop = self.env.loop)

    async def msg_query_handle(self, query):
        # called when the node is the final destination of the query
        #TODO : port management ??
        #TODO : channel management ??
        self.debug("generic msg query handle" + str(query), 'msg')
        if 'method' in query and 'policy' in query and 'port' in query:
            # New 0.2 message format
            self.debug("NEW 2.0 generic msg query handle" + str(query), 'msg')
            if query['method'] in self.methods:
                return await self.methods[query['method']](query)
            else:
                self.warning("Method {} not found to handle query {}".format(query['method'], str(query)), 'msg')
        elif 'port' in query and query['port'] in self.ports:
            port = query['port']
            #self.debug(self.name + ": port = " + str(query), 'msg')
            if query['query'] == 'immediate':
                reply = {'prx_src':self, 'lcid':query['lcid'], 'reply':self.ports[port]['value']}
                #self.debug(self.name + ": immediate reply = " + str(query) + ' ' + str(reply), 'msg')
                await self.msg_send(query['prx_src'], reply)
            else:
                # Subscription
                #self.debug(self.name + ": subscription => " + str(query), 'msg')

                cnx = {'update':True, 'lcid':query['lcid'], 'prx_dst':query['prx_src']}

                # Update back_channels
                key = (id(query['prx_src']), query['lcid'])
                self.back_channels[key] = {'port':query['port'], 'cnx_idx':len(self.ports[port]['connections'])}
                self.debug("Updated back_channels " + str(key) + ' : ' +  str(self.back_channels[key]), 'msg')

                # Add connection to the port
                self.ports[port]['connections'].append(cnx)
                self.debug(self.name + ": subscriptions = " + str(self.ports[port]['connections']), 'msg')

    # async def reply_handle(self, reply):
        # # called when the node is the final destination of the reply
        # pass

    # async def aget(self, portname = None):
        # """Return a ElementTree that represent the Node full state (if possible) or the port value
        # """
        # self.warning("Unimplemented aget() method.")

    # def serialize(self):
        # """
        # """
        # pass

    async def _introspect(self):
        if self.parent is not None:
            parent_name = self.parent.fqn()
        else:
            parent_name = None
        #TODO: links, ports, connections, channels...
        ports = {}
        for portname in self.ports:
            ports[portname] = str(self.ports[portname])
        tasks = {}
        for taskname in self.tasks:
            tasks[taskname] = str(self.tasks[taskname])
        channels = {'test':'dummy'}
        for channel in self.channels:
            self.debug("channel: "+str(channel))
            if isinstance(self.channels[channel], int):
                channels[channel] = "pipe_"+str(self.channels[channel])
            elif isinstance(self.channels[channel], asyncio.Queue):
                channels[channel] = "intern_queue"
            elif isinstance(self.channels[channel], tuple):
                if isinstance(self.channels[channel][0], int):
                    channels[channel] = "wsis: "+str(self.channels[channel][0])+" lcid:"+str(self.channels[channel][1])
                elif isinstance(self.channels[channel][0], Node):
                    channels[channel] = "node: "+str(self.channels[channel][0].fqn())+" lcid:"+str(self.channels[channel][1])
                else:
                    channels[channel] = "coroutine_client"
            else:
                channels[channel] = "unknown"

        return {'class':self.tagname,
                'env':self.env.fqn(),
                'parent':parent_name,
                'name':self.name,
                'ports':ports,
                'tasks':tasks,
                'links':{},
                'connections':{},
                'channels':channels,
                'fqn':self.fqn()}

    # def connect(self, dest, **kwargs):
        # #TODO: whole thing...
        # pass

    def log(self, level, message, logger='main'):
        if len(message) > 511:
            message = message[:508] + '...'
        f = inspect.stack()
        self.env.loggers[logger].log(level, self.fqn() + '.' + f[2][3] + '(): ' + message)

    def debug(self, message, logger='main'):
        self.log(logging.DEBUG, message, logger)

    def info(self, message, logger='main'):
        self.log(logging.INFO, message, logger)

    def warning(self, message, logger='main'):
        self.log(logging.WARNING, message, logger)

    def error(self, message, logger='main'):
        self.log(logging.ERROR, message, logger)
