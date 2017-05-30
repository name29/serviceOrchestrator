"""
Created on Apr 12, 2016

@author: gabrielecastellano
"""

from doubledecker.clientSafe import ClientSafe
import logging
import json

from .domain_info import DomainInfo
from .sql.domain import Domain
from .sql.domains_info import DomainInformation
from .authentication_graph_manager import AuthGraphManager

class DDClient(ClientSafe):

    def __init__(self, name, dealer_url, customer, keyfile):
        super().__init__(name, dealer_url, customer, keyfile)
        logging.info("Doubledecker Client State: disconnected")

    def on_data(self, dst, msg):
        print(dst, " sent", msg)

    def on_discon(self):
        logging.info("Doubledecker Client State: disconnected")

    def on_pub(self, src, topic, msg):
        # new domain information
        msg_str = "PUB %s from %s" % (str(topic), str(src))
        print(msg_str)
        # TODO validate message

        try:
            domain = src.decode("utf-8")
            domain_info = json.loads(msg.decode("utf-8"))
        except:
            pass

    # dd ClientSafe call this method without src and msg parameters, so if i override correctly with
    # this parameters (as requested from ClientInterface), there will be an error at any registration
    # and there will be a registration infinite loop.
    # TODO publish an issue on dd repository
    def on_reg(self):
        logging.info("Doubledecker Client State: connected")
        self.subscribe("frog:domain-description", "/0/0/0/")

    def unsubscribe(self, topic, scope):
        pass

    def on_error(self, code, msg):
        pass