# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:47:29 2018

"""

from .node import *

class Container(Node):
    tagname = "container"
    def __init__(self, contents = None, elt = None, **kwargs):
        super().__init__(**kwargs)

        # links between container ports and contained nodes ports
        self.inside_links = {}

        if contents is None:
            # a brand (and empty) new container
            #TODO
            self.contents = {}
            pass
        else:
            # get container content from argument
            #TODO
            pass
        if elt is not None:
            self.populate(elt)

    def populate(self, root):
        for branch in root:
            if branch.tag == 'nodes':
                for node in branch:
                    self.debug("Child Node :"+str(node.tag)+' '+str(node.attrib))
                    if node.tag in self.env.registry:
                        self[node.attrib['name']] = self.env.registry[node.tag](env=self.env, parent=self, elt=node, **node.attrib)
                    else:
                        self.warning("Application : Unable to instanciate node for '{}' tag".format(node.tag))
            elif branch.tag == 'ports':
                for port in branch:
                    self.debug("Container Port :"+str(port.tag)+' '+str(port.attrib))
                    self.inside_links[port.attrib['name']] = (self[port.attrib['node']], port.attrib['port'])

    def node_add(self, name, node):
        "Add a named node to the container"
        #TODO: Check if node already exists
        #TODO: Check node type
        #TODO: Check name type
        self.contents[name] = node

    async def msg_query_handle(self, query):
        self.debug('query = ' + str(query), 'msg')
        if query['port'] in self.inside_links:
            self.debug('linked ' + str(self.inside_links), 'msg')
            base_port = query['port']
            query['port'] = self.inside_links[base_port][1]
            await self.msg_queue_delegate(self.inside_links[base_port][0], query)
        else:
            await super().msg_query_handle(query)

    # async def msg_handle(self, msg):
        # if 'node' in msg and msg['node'] == self.name:
            # # This node is the final destination
            # # TODO
            # pass
        # else:
            # if 'dst' in msg and msg['dst'].split('/')[0] in self.contents:
                # # reroute to contained
                # pass
        # await super().msg_handle(msg)

    # def get(self):
        # #return node content (a list of etree elements)
        # #TODO
        # return []

    def __setitem__(self, key, value):
        self.contents[key] = value

    def __getitem__(self, key):
        return self.contents[key]

    def __delitem__(self, key):
        del self.contents[key]

    def __contains__(self, key):
        return key in self.contents

    async def _introspect(self, args={}):
        ret = await super()._introspect()
        nodes = {}
        for key, value in self.contents.items():
            nodes[key] = await self.msg_query(value, {'url':key, 'policy':'immediate', 'method':'get', 'port':'state'}, timeout = 2.)
            #nodes[key] = await value._introspect()
        ret['nodes'] = nodes
        return ret

    def run(self):
        super().run()
        for childname in self.contents:
            self.contents[childname].run()
