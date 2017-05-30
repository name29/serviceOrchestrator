"""
Created on Oct 1, 2014
@author: fabiomignini
@author: gabrielecastellano
"""

import logging
import requests
import time

from threading import Thread

from nffg_library.nffg import NF_FG, VNF, Port,EndPoint,FlowRule,Match,Action

from vnf_template_library.template import Template

from ServiceOrchestrator.Configuration import Configuration
from ServiceOrchestrator.InfrastructureOrchestratorUniversalNode import InfrastructureOrchestratorUniversalNode
from ServiceOrchestrator.ConnectionException import ConnectionException
from ServiceOrchestrator.DatastoreClient import DatastoreClient


def disconnectPort(nffg,portId):
    if ( not deploy_nffg.existPort(portId) ):
        raise Exception("Port with id:"+portId+" is invalid")
    deploy_nffg.deleteIncomingFlowrules(portId)
    deploy_nffg.deleteOutcomingFlowrules(portId)

def linkPorts(nffg,flowId1,flowId2,port1,port2):
    if ( not deploy_nffg.existPort(port1) ):
        raise Exception("Port with id:"+port1+" is invalid")

    if ( not deploy_nffg.existPort(port2) ):
        raise Exception("Port with id:"+port2+" is invalid")

    deploy_nffg.addFlowRule(
        FlowRule(flowId1, 1, Match(port1), [Action(port2)]))
    deploy_nffg.addFlowRule(
        FlowRule(flowId2, 1, Match(port2), [Action(port1)]))

import json

# from ServiceOrchestrator.DDClient import DDClient

try:
    conf = Configuration('config/default-config.ini')
except Exception as e:
    logging.error("Unable to load configuration: "+e.message);
    quit(1)

# set log level
if conf.DEBUG is True:
    log_level = logging.DEBUG
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
elif conf.VERBOSE is True:
    log_level = logging.INFO
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
else:
    log_level = logging.WARNING

# format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

logging.basicConfig(filename=conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Service Orchestrator Starting")
print("Welcome to the User-oriented Service Orchestrator Application")
logging.info("Starting Service Orchestrator application")

# start the dd client to receive information about domains
#base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
#dd_client = DDClient(conf.DD_NAME, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
#thread = Thread(target=dd_client.start)
#thread.start()

datastore = DatastoreClient("http://selforch.name29.net:8081")

template_host = datastore.getTemplate("host_VNF")
template_nat = datastore.getTemplate("nat")
template_switch = datastore.getTemplate("switch")
template_orch = datastore.getTemplate("serviceorch")

host_vnf = template_host.getVNF("HOST","host_VNF")
server_vnf = template_host.getVNF("SERVER","server")
nat_vnf = template_nat.getVNF("NAT","nat")
switch_vnf = template_switch.getVNF("SWITCH","switch")
orch_vnf = template_orch.getVNF("SELFORCH","serviceorch")

managment_endpoint = EndPoint("MANAGMENT_ENDPOINT","","host-stack",configuration="static",ipv4="192.168.40.1/24")


deploy_nffg = NF_FG("1","test_nffg_nat")


deploy_nffg.addVNF(host_vnf)
deploy_nffg.addVNF(server_vnf)
deploy_nffg.addVNF(orch_vnf)
deploy_nffg.addVNF(nat_vnf)
deploy_nffg.addVNF(switch_vnf)
deploy_nffg.addEndPoint(managment_endpoint)

linkPorts(deploy_nffg,"HOST_NAT","NAT_HOST","vnf:HOST:inout:0","vnf:NAT:User:1")
linkPorts(deploy_nffg,"SERVER_NAT","NAT_SERVER","vnf:SERVER:inout:0","vnf:NAT:WAN:0")
linkPorts(deploy_nffg,"SWITCH_ENDPOINT","ENDPOINT_SWITCH","vnf:SWITCH:port1:0","endpoint:MANAGMENT_ENDPOINT")
linkPorts(deploy_nffg,"SWITCH_NAT","NAT_SWITCH","vnf:SWITCH:port2:1","vnf:NAT:MAN:2")
linkPorts(deploy_nffg,"SWITCH_SELFORCH","SELFORCH_SWITCH","vnf:SWITCH:port3:2","vnf:SELFORCH:inout:0")

try:
    orchestrator = InfrastructureOrchestratorUniversalNode("admin","admin","selforch.name29.net",8080,30000)
    orchestrator.addNFFG(deploy_nffg)
except ConnectionException as ex:
    print ex.message
    exit(1)
except requests.exceptions.HTTPError as ex:
    print ex.message
    exit(1)

print "Wait 5 seconds.."
#time.sleep(5)


natDUP_vnf = template_nat.getVNF("NATDUP","natDUP")
switchIN_vnf = template_switch.getVNF("SWITCHIN","switchIN")
switchOUT_vnf = template_switch.getVNF("SWITCHOUT","switchOUT")

deploy_nffg.addVNF(natDUP_vnf)
deploy_nffg.addVNF(switchIN_vnf)
deploy_nffg.addVNF(switchOUT_vnf)

disconnectPort(deploy_nffg,"vnf:HOST:inout:0")
disconnectPort(deploy_nffg,"vnf:SERVER:inout:0")
disconnectPort(deploy_nffg,"vnf:NAT:User:1")
disconnectPort(deploy_nffg,"vnf:NAT:WAN:0")

linkPorts(deploy_nffg,"HOST_SWITCHIN","SWITCHIN_HOST","vnf:HOST:inout:0","vnf:SWITCHIN:port1:0")
linkPorts(deploy_nffg,"NAT_SWITCHIN","SWITCHIN_NAT","vnf:NAT:User:1","vnf:SWITCHIN:port2:1")
linkPorts(deploy_nffg,"NATDUP_SWITCHIN","SWITCHIN_NATDUP","vnf:NATDUP:User:1","vnf:SWITCHIN:port3:2")

linkPorts(deploy_nffg,"SERVER_SWITCHOUT","SWITCHOUT_SERVER","vnf:SERVER:inout:0","vnf:SWITCHOUT:port1:0")
linkPorts(deploy_nffg,"NAT_SWITCHOUT","SWITCHOUT_NAT","vnf:NAT:WAN:0","vnf:SWITCHOUT:port2:1")
linkPorts(deploy_nffg,"NATDUP_SWITCHOUT","SWITCHOUT_NATDUP","vnf:NATDUP:WAN:0","vnf:SWITCHOUT:port3:2")

linkPorts(deploy_nffg,"NATDUP_SWITCH","SWITCH_NATDUP","vnf:NATDUP:MAN:2","vnf:SWITCH:port4:3")

try:
    orchestrator.addNFFG(deploy_nffg)
except ConnectionException as ex:
    print ex.message
    exit(1)
except requests.exceptions.HTTPError as ex:
    print ex.message
    exit(1)


print "Fine"