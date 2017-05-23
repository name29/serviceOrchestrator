"""
Created on Oct 1, 2014
@author: fabiomignini
@author: gabrielecastellano
"""
import configparser
import inspect
import json
import os


class Configuration(object):
    _instance = None
    _AUTH_SERVER = None
    config_file = 'config/default-config.ini'

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super(Configuration, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._AUTH_SERVER is None:
            self.inizialize()

    def inizialize(self):

        config = configparser.RawConfigParser()
        base_folder = \
        os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])).rpartition('/')[0]
        config.read(base_folder + '/' + Configuration.config_file)
        self._LOG_FILE = config.get('log', 'log_file')
        self._VERBOSE = config.getboolean('log', 'verbose')
        self._DEBUG = config.getboolean('log', 'debug')
        self._DB_CONNECTION = config.get('db', 'connection')
        self._NOBODY_USERNAME = config.get('nobody', 'username')
        self._NOBODY_PASSWORD = config.get('nobody', 'password')
        self._NOBODY_TENANT = config.get('nobody', 'tenant')
        self._ADMIN_NAME = config.get('admin', 'admin_name')

        self._ISP_USERNAME = config.get('ISP', 'username')
        self._ISP_PASSWORD = config.get('ISP', 'password')
        self._ISP_TENANT = config.get('ISP', 'tenant')

        # ports
        self._INGRESS_TYPE = config.get('user_connection', 'ingress_type')
        self._EGRESS_PORT = config.get('user_connection', 'egress_port')
        self._EGRESS_TYPE = config.get('user_connection', 'egress_type')
        self._CP_CONTROL_PORT = config.get('user_connection', 'cp_control_port')
        self._CP_CONTROL_TYPE = config.get('user_connection', 'cp_control_type')

        self._SWITCH_NAME = [e.strip() for e in config.get('switch', 'switch_l2_name').split(',')]
        self._CONTROL_SWITCH_NAME = config.get('switch', 'switch_l2_control_name')

        self._SERVICE_LAYER_IP = config.get('service_layer', 'ip')
        self._SERVICE_LAYER_PORT = config.get('service_layer', 'port')

        self._DD_NAME = config.get('doubledecker', 'dd_name')
        self._DD_CUSTOMER = config.get('doubledecker', 'dd_customer')
        self._BROKER_ADDRESS = config.get('doubledecker', 'broker_address')
        self._DD_KEYFILE = config.get('doubledecker', 'dd_keyfile')

        self._DEBUG_MODE = config.getboolean('orchestrator', 'debug_mode')

        self._ORCH_PORT = config.get('orchestrator', 'port')
        self._ORCH_IP = config.get('orchestrator', 'ip')
        self._ORCH_TIMEOUT = config.get('orchestrator', 'timeout')

        self._CAPTIVE_PORTAL_IP = config.get('captive_portal', 'ip')

        self._FLOW_PRIORITY = config.get('user_connection', 'flow_priority')
        self._SWITCH_TEMPLATE = config.get('switch', 'template')
        self._DEFAULT_PRIORITY = config.get('flowrule', "default_priority")

        self._ENRICH_USER_GRAPH = config.getboolean('other_settings', 'enrich_user_graph')
        self._BLIND_ISP_DEPLOYMENT = config.getboolean('other_settings', 'blind_isp_deployment')
        self._INGRESS_GRAPH_FILE = config.get('ingress_nf_fg', "file")
        self._EGRESS_GRAPH_FILE = config.get('engress_nf_fg', "file")

        # End-point types
        self._SG_USER_INGRESS = config.get('endpoint_type', 'sg_user_ingress')
        self._SG_USER_EGRESS = config.get('endpoint_type', 'sg_user_egress')
        self._USER_INGRESS = config.get('endpoint_type', 'user_ingress')
        self._REMOTE_USER_INGRESS = config.get('endpoint_type', 'remote_user_ingress')
        self._USER_EGRESS = config.get('endpoint_type', 'user_egress')
        self._ISP_INGRESS = config.get('endpoint_type', 'isp_ingress')
        self._ISP_EGRESS = config.get('endpoint_type', 'isp_egress')
        self._CONTROL_INGRESS = config.get('endpoint_type', 'control_ingress')
        self._CONTROL_EGRESS = config.get('endpoint_type', 'control_egress')
        self._CP_CONTROL = config.get('endpoint_type', 'cp_control')

        # Orchestrator
        self._ISP = config.getboolean('orchestrator', 'isp')
        self._NOBODY = config.getboolean('orchestrator', 'nobody')

        self._VNF_AWARE_DOMAINS = json.loads(config.get('other_settings', 'vnf_aware_domains'))
