#!/usr/bin/env python3

"""Provide communication functionality between each host"""

import logging
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Create local logging object
logger = logging.getLogger(__name__)

class Error(object):
    UNKNOWN_ERROR = 1
    NOT_IMPLEMENTED = 2

    strerror_dict = {UNKNOWN_ERROR: "Unknown error.",
                     NOT_IMPLEMENTED: "Request not implemented."}

    def strerror(self, error):
        try:
            return Error.strerror_dict[error]
        except KeyError:
            return "Unknown error code"

class RPCServerHandler(SimpleXMLRPCRequestHandler):
    """Class that defines the server behavior for each connection"""

    def setup(self):
        logger.debug('{}:{} connected'.format(*self.client_address))
        super(RPCServerHandler, self).setup()

    def finish(self):
        logger.debug('{}:{} disconnect'.format(*self.client_address))
        super(RPCServerHandler, self).finish()

class RPCThreadingServer(ThreadingMixIn, SimpleXMLRPCServer):
    """Class to create the server"""
    pass

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
