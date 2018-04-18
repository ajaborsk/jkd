from urllib.parse import urlparse
import inspect
import asyncio
import logging
import traceback
import time
import sys

import xml.etree.ElementTree as ET

class JkdSendError(Exception):
    pass

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
    def __init__(self, env = None, parent = None, name = '', elt = None):
        #print("setting env to", env)
        self.env = env
        self.parent = parent
        self.name = name
        self.debug(str(self.__class__) + " fqn: " + self.fqn())

        self.force_debug = False
        self.do_debug = False

        # Next available Local Channel ID (lcid)
        self.next_lcid = 0
        # Global input messages queue
        self.input = asyncio.Queue()
        # I/O ports. each port has a entry in the dictionary : 'portname':{properties}
        self.ports = {}
        self.tasks = {}
        self.methods = {'get':self.method_get,
                        'put':self.method_put}

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
        self.task_add('_on_update_loop', coro = self._on_update_loop)
        self.task_add('_state', coro = self._introspect, returns = ['state'])

        self.links = {}
        if elt is not None:
            for branch in elt:
                if branch.tag == 'links':
                    for link_node in branch:
                        port_name = link_node.attrib.get('input')
                        self.links[port_name] = dict(link_node.attrib)
                        # No check for now (will be done in self.run() preparation part)
                        self.debug('link: '+str(port_name)+' <== '+str(self.links[port_name]))

    def _task_done_callback(self, future):
        e = future.exception()
        if e is not None:
            self.warning(repr(e))
            stack = future.print_stack()
#            for frame in traceback.format_list(stack):
#                self.warning("  "+str(frame))

    def task_add(self, taskname, coro = None, gets = [], returns = [], needs = [], provides = [], autolaunch = False, client = None):
        """Add a task to node tasks list
        """
        self.tasks[taskname] = {'coro':coro,
                                'gets':gets,
                                'returns':returns,
                                'needs':needs,
                                'provides':provides,
                                'autolaunch':autolaunch,
                                'client':client,
                                'task':None }

    async def _wait_for_port(self, portname, client = None):
        return (portname, await self.port_get(portname)['queue'].get(), client)

    def port_add(self, portname, mode = 'output', cached = False, timestamped = False, auto = False, client = None):
        self.ports[portname] = { 'mode': mode,
                                 'cached': cached,
                                 'value': None,
                                 'timestamped': timestamped,
                                 'auto': auto,
                                 'client': client,
                                 'connections':[]}

    def port_get(self, portname):
        if portname in self.ports:
            return self.ports[portname]
        else:
            self.warning("port '" + str(portname)+ "' does not exist")
            return None

    async def port_input_get(self, portname, args = None):
        if portname in self.links:
            self.debug('  link found: '+str(self.links[portname]))
            #text = await self.msg_query(app, {'method':'get', 'policy':'immediate', 'src':self.fqn(), 'url':msg_url, 'port':port_name, 'args':dict(request.query)}, timeout = 5.)
            msg = {'method':'get', 'policy':'immediate', 'flags':'c', 'url':self.links[portname]['node'], 'port':self.links[portname]['port']}
            # propagate query_args
            if args is not None:
                msg['args'] = args
            #TODO: define a timeout policy instead of spreading 50. everywhere...
            resp = await self.msg_query(self.parent, msg, timeout = 50.)
            return resp
        else:
            return None

    async def port_read(self, portname):
        queue = self.port_get(portname).get('queue')
        if queue is not None:
            return await queue.get()
        else:
            self.error('no intern queue for port: '+str(portname))

    async def port_write(self, portname, value):
        # default action : do nothing
        pass

    async def port_output(self, port, value):
        # Triggers output connections
        #TODO: fire also connections/queues of overlapping ports
        for cnx in port['connections']:
            self.debug('cnx: '+str(cnx))
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
                self.debug(str(self.name) + " : output_msg to "+str(cnx['prx_dst'])+': '+str(msg))
                await self.msg_send(cnx['prx_dst'], msg)
                #TODO: handle send error (dst does not exist, for instance)


    async def port_value_update(self, portname, value, from_inside = False):
        #self.debug('portname: '+str(portname))
        port = self.port_get(portname)
        #self.debug('port: '+str(port))
        if port.get('cached', False):
            port['value'] = value
            #self.debug('port:'+str(port)+' '+str(self.ports[portname]))

        # internal stuff...
        if not from_inside:
            await self.port_write(portname, value)

        queue = port.get('queue')
        if isinstance(queue, asyncio.Queue):
            #self.debug('write to intern port queue: '+str(value))
            if queue.full():
                # make some place...
                queue.get_nowait()
            queue.put_nowait(value)

        # external stuff
        await self.port_output(port, value)

        return value

    async def _on_update_loop(self, inputs = [], outputs = [], coro = None, args = {}, client = None):
        self.debug('coro: '+repr(coro)+' inputs: '+str(inputs)+', outputs:'+str(outputs))
        done = False
        xref = {name:inputs.index(name) for name in inputs}
        kwargs = {}
        if args is not None:
            kwargs['args'] = args
        if client is not None:
            kwargs['client'] = client
        process_args = []
        # "get" a initial value for every port
        for input_port in inputs:
            process_args.append(await self.port_read(input_port))
        while not done:
            self.debug('process... '+str(coro)+', args='+str(process_args))
            task = coro(*process_args, **kwargs)
            if inspect.iscoroutine(task):
                results = await task
                self.debug('processed. results = '+str(results))
                if len(outputs) == 1:
                    await self.port_value_update(outputs[0], results)
                else:
                    for i in range(len(outputs)):
                        await self.port_value_update(outputs[i], results[i])
            elif inspect.isasyncgen(task):
                async for results in task:
                    self.debug('processed. results = '+str(results))
                    if len(outputs) == 1:
                        await self.port_value_update(outputs[0], results)
                    else:
                        for i in range(len(outputs)):
                            await self.port_value_update(outputs[i], results[i])

            # If there is no input => Do not enter into a infinite loop
            if len(inputs) == 0:
                done = True
            else:
                self.debug('Waiting for *any* input update...'+repr(inputs))
                wait_list = []
                for portname in inputs:
                    if 'queue' in self.ports[portname]:
                        wait_list.append(self._wait_for_port(portname))
                self.debug("-*-*- Entering ")
                done_tasks, pending = await asyncio.wait(wait_list, return_when = asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                for d in done_tasks:
                    r = d.result()
                self.debug("T: "+str(r[0])+' '+str(r[1]))
                self.debug("-*-*- Exited ")
                process_args[xref[r[0]]] = r[1]
                self.debug("xref" + repr(xref))
                self.debug("args: "+repr(process_args))
                # #TODO
                # args = []
                # for input_port in inputs:
                    # args.append(await self.port_read(input_port))

    async def link_connect(self, linkname):
        #TODO
        pass

    def run(self):
        # prepare : check input links
        #TODO

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

        if self.env is not None and hasattr(self.env, 'loop'):
            # Launch autolaunch tasks
            for taskname in self.tasks:
                if self.tasks[taskname].get('autolaunch'):
                    self.debug("(auto)launching task: " + taskname)
                    self.tasks[taskname]['task'] = self.env.loop.create_task(self.tasks[taskname]['coro']())
                    self.tasks[taskname]['task'].add_done_callback(self._task_done_callback)
            # Launch autolaunch tasks
            for portname in self.links:
                link = self.links[portname]
                if link.get('connect') == 'auto':
                    self.debug("(auto)connecting port: " + portname)
                    t = self.env.loop.create_task(self.msg_query(self.parent, {'method':'get', 'policy':link['policy'], 'flags':'c', 'path':link['node'], 'port':link['port']}, coro=self.port_updated, client = portname))
                    t.add_done_callback(self._task_done_callback)

    def stop(self):
        #TODO
        pass

    #TODO:  An API to add/remove/configure ports

    def fqn(self):
        "Fully Qualified Name"
        if self.parent is None:
            return(self.name)
        else:
            return self.parent.fqn() + '/' + self.name

    async def port_updated(self, msg, portname):
        await self.port_value_update(portname, msg['reply'])

    async def method_get(self, msg):
        self.debug("msg: "+str(msg), 'msg')
        portname = msg['port']
        port = self.port_get(portname)
        query_args = msg.get("args", None)
        if port is None:
            self.warning('Trying to get value of unknown port "{}"'.format(portname), 'msg')
            response = {'flags':'d', 'prx_src':self, 'lcid':msg['lcid'], 'error':'Unknown port '+str(portname)}
            await self.msg_send(msg['prx_src'], response)
            self.debug("Replied with:"+str(response), 'msg')
        self.debug('policy =' + str(msg['policy']) + ' port=' + str(portname), 'msg')
        if msg['policy'] == 'immediate':
            # Check if a task provides the port value.
            if 'provided_by' in port:
                # Port is *provided* by a task
                if port['cached']:
                    task = self.tasks[port['provided_by']]
                    if task['task'] is None:
                        # Get needed parameters for task
                        args = []
                        for arg in task['gets']:
                            self.warning("TODO")
                        # Launch task
                        self.debug('Launching task: '+str(port['provided_by'])+' '+str(task['coro']))
                        task['task'] = self.env.loop.create_task(task['coro'](args=query_args))
                        task['task'].add_done_callback(self._task_done_callback)
                        self.debug('Launched task: '+str(port['provided_by']))
                        #TODO : How to stop this task ?
                    #TODO : Wait for task do its job !
                    await asyncio.sleep(0.1)
                    result = port['value']
                else:
                    self.warning("TODO")
            elif 'returned_by' in port:
                self.debug("returned_by mode: "+str(msg), 'msg')
                # Port is *returned* by a task
                task = self.tasks[port['returned_by']]
                # Get needed parameters for task
                args = []
                for arg in task['gets']:
                    self.debug('Getting arg/port: '+str(arg))
                    if arg in self.links:
                        #TEST
                        self.debug('  link found: '+str(self.links[arg]))
                        #text = await self.msg_query(app, {'method':'get', 'policy':'immediate', 'src':self.fqn(), 'url':msg_url, 'port':port_name, 'args':dict(request.query)}, timeout = 5.)
                        arg_msg = {'method':'get', 'policy':'immediate', 'flags':'c', 'url':self.links[arg]['node'], 'port':self.links[arg]['port']}
                        # propagate query_args
                        if query_args is not None:
                            arg_msg['args'] = query_args
                        #TODO: define a timeout policy instead of spreading 50. everywhere...
                        resp = await self.msg_query(self.parent, arg_msg, timeout = 50.)
                        args.append(resp)
                # Launch task
                kwargs = {}
                if query_args is not None:
                    kwargs['args'] = query_args
                if task['client'] is not None:
                    kwargs['client'] = task['client']
                task = task['coro'](*args, **kwargs)
                if inspect.iscoroutine(task):
                    self.debug("launching (coroutine) task: "+str(task)+' args:'+str(args)+' kwargs:'+str(kwargs))
                    result = await task
                    if len(self.tasks[port['returned_by']]['returns']) != 1:
                        idx = self.tasks[port['returned_by']]['returns'].index(portname)
                        result = result[idx]
                    response = {'flags':'d', 'prx_src':self, 'lcid':msg['lcid'], 'reply':result}
                    #response = {'flags':'d', 'prx_src':self, 'prx_dst':msg['prx_src'], 'lcid':msg['lcid'], 'reply':result}
                    await self.msg_send(msg['prx_src'], response)
                    self.debug("Replied with:" + str(response), 'msg')
                elif inspect.isasyncgen(task):
                    self.debug("launching (generator) task: "+str(task)+' args:'+str(args)+' kwargs:'+str(kwargs))
                    async for result in task:
                        if len(self.tasks[port['returned_by']]['returns']) != 1:
                            idx = self.tasks[port['returned_by']]['returns'].index(portname)
                            result = result[idx]
                        response = {'flags':'d', 'prx_src':self, 'lcid':msg['lcid'], 'reply':result}
                        #response = {'flags':'d', 'prx_src':self, 'prx_dst':msg['prx_src'], 'lcid':msg['lcid'], 'reply':result}
                        await self.msg_send(msg['prx_src'], response)
                        self.debug("Replied with:" + str(response), 'msg')
            else:
                self.warning('port "{}" is not provided nor returned by any task.'.format(portname))
                return None
        elif msg['policy'] == 'on_update':
            if 'provided_by' in port:
                self.debug("provided_by mode: "+str(msg), 'msg')
                task = self.tasks[port['provided_by']]
                needs = task['needs']
                kwargs = {}
                if query_args is not None:
                    kwargs['args'] = query_args
                if task['client'] is not None:
                    kwargs['client'] = task['client']
            elif 'returned_by' in port:
                self.debug('returns_by mode - internal loop on process task')
                needs = self.tasks[port['returned_by']]['gets']
                # if len(needs) == 0:
                    # # If process tasks needs no input then do not launch loop task => nothing to do
                    # task = None
                # else:
                task = self.tasks['_on_update_loop']
                kwargs = {'args':msg.get('args', {}), 'coro':self.tasks[port['returned_by']]['coro'], 'inputs':needs, 'outputs':self.tasks[port['returned_by']]['returns'], 'client':self.tasks[port['returned_by']]['client']}
                if query_args is not None:
                    kwargs['args'] = query_args
                if task['client'] is not None:
                    kwargs['client'] = task['client']
            else:
                self.warning('Unable to reply for on_update policy: '+str(msg))
                return

            if task is not None and task['task'] is None:
                # The task isn't running => launch it
                # Prepare source data
                for need in needs:
                    self.debug('needs: '+str(need))
                    link = self.links[need]
                    #TODO: test if launching a new subscription is needed
                    if True:
                        self.port_get(need)['queue'] = asyncio.Queue(maxsize = 1)
                        #self.debug('ports: '+str(self.ports))
                        await self.msg_query(self.parent, {'method':'get', 'policy':'on_update', 'flags':'c', 'path':link['node'], 'port':link['port'], 'args':query_args}, coro=self.port_updated, client = need)
                #TODO
                # Launch task

                self.debug('Launching task: '+str(task['coro']))
                task['task'] = self.env.loop.create_task(task['coro'](**kwargs))
                task['task'].add_done_callback(self._task_done_callback)
                self.debug('Launched task.')

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

            # If output is cached AND a value has already been set, then send a first reply
            if port.get('cached', False) and port.get('value', None) is not None:
                response = {'flags':'f', 'prx_src':self, 'lcid':msg['lcid'], 'reply':port.get('value', None)}
                await self.msg_send(msg['prx_src'], response)
        else:
            self.warning("Unhandled policy: "+str(msg['policy']))

    async def method_put(self, msg):
        self.debug("msg: "+str(msg), 'msg')

        value = await self.port_value_update(msg['port'], msg['args']['value'])

        # Send reply
        response = {'flags':'d', 'prx_src':self, 'lcid':msg['lcid'], 'reply':value}
        #response = {'flags':'d', 'prx_src':self, 'prx_dst':msg['prx_src'], 'lcid':msg['lcid'], 'reply':result}
        await self.msg_send(msg['prx_src'], response)
        self.debug("Replied with:"+str(response), 'msg')

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
        try:
            await destination.input.put(msg)
        except:
            # send error
            #TODO: remove (back) channel ??
            raise JkdSendError("cannot send message to (queue) destination")
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
            #self.debug('Waiting for message...', 'msg')
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
            t = self.env.loop.create_task(self.msg_queue_handle(msg))
            t.add_done_callback(self._task_done_callback)

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
                try:
                    if elt in self:
                        await self.msg_reroute(self[elt], msg)
                    else:
                        self.warning('No route for '+str(msg), 'msg')
                except TypeError:
                    self.warning('No route for '+str(msg), 'msg')

        elif 'reply' in msg:
            # This is a reply
            self.debug(' reply catched : ' + str(msg), 'msg')
            lcid = msg['lcid']
            if lcid in self.channels:
                if isinstance(self.channels[lcid], asyncio.Queue):
                    self.debug(' reply queue mode : ' + str(msg), 'msg')
                    # The node is the final destination (queue mode)
                    await self.channels[lcid].put(msg)
                elif isinstance(self.channels[lcid], tuple):
                    self.debug(' reply coro mode : ' + str(msg), 'msg')
                    self.debug('       coro = ' + repr(self.channels[lcid][0]), 'msg')

                    # The node is the final destination (coroutine mode)
                    await self.channels[lcid][0](msg, self.channels[lcid][1])
                else:
                    # Just route to next node
                    self.debug(' reply route mode : ' + str(msg), 'msg')
                    msg['lcid'] = self.channels[lcid]['lcid']
                    msg['prx_src'] = self
                    await self.msg_send(self.channels[lcid]['prx_dst'], msg)
                # if 'eoq' in msg and msg['eoq'] == True:
                    # # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    # del self.channels[lcid]
        elif 'error' in msg:
            # This is a (replied) error
            if 0:
                # The node is the final destination
                #TODO: handle error locally
                pass
            else:
                # Just route to next node
                #TODO: route error to next node in channel
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

    async def _introspect(self, args={}):
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
        sys.abort()
