# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:47:29 2018

"""

from .node import *

class Container(Node):
    tagname = "container"
    def __init__(self, contents = None, elt = None, **kwargs):
        super().__init__(**kwargs)
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
        for child in root:
            self.debug("Child :"+str(child.tag)+' '+str(child.attrib))
            if child.tag in self.env.registry:
                self[child.attrib['name']] = self.env.registry[child.tag](env=self.env, parent=self, elt=child, **child.attrib)
            else:
                self.warning("Application : Unable to instanciate node for '{}' tag".format(child.tag))

    def node_add(self, name, node):
        "Add a named node to the container"
        #TODO: Check if node already exists
        #TODO: Check node type
        #TODO: Check name type
        self.contents[name] = node

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

    def get(self):
        #return node content (a list of etree elements)
        #TODO
        return []

    def __setitem__(self, key, value):
        self.contents[key] = value

    def __getitem__(self, key):
        return self.contents[key]

    def __delitem__(self, key):
        del self.contents[key]

    def __contains__(self, key):
        return key in self.contents

    async def _introspect(self):
        ret = await super()._introspect()
        nodes = {}
        for key, value in self.contents.items():
            nodes[key] = await value._introspect()
        ret['nodes'] = nodes
        return ret

