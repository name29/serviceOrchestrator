"""
Created on Oct 1, 2014
@author: fabiomignini
@author: gabrielecastellano
"""

#Tutti i nat lato LAN hanno lo stesso ip e lo stesso mac-address

import logging
import requests
import time
import json

# from ServiceOrchestrator.DDClient import DDClient

from nffg_library.nffg import NF_FG, VNF, Port,EndPoint,FlowRule,Match,Action

from ServiceOrchestrator.ConfigurationSDN import ConfigurationSDN
from ServiceOrchestrator.InfrastructureOrchestrator import InfrastructureOrchestrator
from ServiceOrchestrator.ConnectionException import ConnectionException
from ServiceOrchestrator.DatastoreClient import DatastoreClient
from ServiceOrchestrator.IpPool import IpPool
from ServiceOrchestrator.ConfigurationService import ConfigurationService
from ServiceOrchestrator.LoadBalancer import LoadBalancerL2


def buildVNF(template, vnf_id, vnf_name):
    vnf_ports = []
    # TODO
    for port in template.ports:
        port_range = port.position.split('-')
        if port_range[1] == 'N':
            raise Exception("Unable to generate port")

        i_from = int(port_range[0])
        i_to = int(port_range[1])
        for portId in range(i_from, i_to + 1):
            vnf_ports.append(Port(port.label + ':' + str(portId - 1)))
            # print "Adding port "+port.label+':'+str(portId-1)+" to "+vnf_id+"/"+vnf_name

    vnf_id = vnf_id
    vnf = VNF(_id=vnf_id, name=vnf_name, vnf_template_location=template.name, ports=vnf_ports)
    return vnf

def add_host(orchestrator,datastore,nffg_name):
    try:
        nffg = orchestrator.getNFFG(nffg_name)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    x=0
    hosts = nffg.getVNFStartWith("HOST_")
    SWITCH_LAN_vnf = nffg.getVNF("SWITCH_LAN")
    SWITCH_MAN_vnf = nffg.getVNF("SWITCH_MAN")

    if ( hosts is None):
        print "Errore, impossibile trovare una VNF che inizia con 'HOST_'"
        exit(1)

    for host in hosts:
        id = host.id.split("HOST_")[1]

        if int(id) > x:
            x = int(id)

    x = x + 1

    template_host = datastore.getTemplate("host_VNF")
    host_vnf = buildVNF(template_host,"HOST_"+str(x), "HOST_"+str(x))

    nffg.addVNF(host_vnf)

    linkPorts(nffg,"HOST"+str(x)+"_SWITCH_LAN","SWITCH_LAN_HOST"+str(x),host_vnf.getFullnamePortByLabel("inout"),SWITCH_LAN_vnf.getFullnamePortByLabel(SWITCH_LAN_vnf.getFreePort(nffg,"port")))
    linkPorts(nffg, "SWITCH_MAN_HOST"+str(x), "HOST"+str(x)+"_SWITCH_MAN",SWITCH_MAN_vnf.getFullnamePortByLabel(SWITCH_MAN_vnf.getFreePort(nffg, "port")),host_vnf.getFullnamePortByLabel("management"))

    try:
        orchestrator.addNFFG(nffg)
    except ConnectionException as ex:
        print ex.message
        exit(1)
    except requests.exceptions.HTTPError as ex:
        print ex.message
        exit(1)

def remove_host(orchestrator,nffg_name):
    try:
        nffg = orchestrator.getNFFG(nffg_name)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    hosts = nffg.getVNFStartWith("HOST_")

    nffg.removeVNF(hosts[-1].id)

    try:
        orchestrator.addNFFG(nffg)
    except ConnectionException as ex:
        print ex.message
        exit(1)
    except requests.exceptions.HTTPError as ex:
        print ex.message
        exit(1)

def disconnectPort(nffg, portId):
    if not nffg.existPort(portId) :
        raise Exception("Port with id:"+portId+" is invalid")
    nffg.deleteIncomingFlowrules(portId)
    nffg.deleteOutcomingFlowrules(portId)

def linkPorts(nffg, flowId1, flowId2, port1, port2):
    if  not nffg.existPort(port1) :
        raise Exception("Port with id:"+port1+" is invalid")

    if not nffg.existPort(port2) :
        raise Exception("Port with id:"+port2+" is invalid")

    nffg.addFlowRule(
        FlowRule(flowId1, 1, Match(port1), [Action(port2)]))
    nffg.addFlowRule(
        FlowRule(flowId2, 1, Match(port2), [Action(port1)]))

nffg_id = "1"
nffg_name = "test_nffg_nat"
tenant_id = 2
nat_mac = "02:01:02:03:04:05"
nat_lan = { "ip": "192.168.10.1", "netmask":"255.255.255.0" }

datastore_url = "http://selforch.name29.net:8081"
datastore_username = "admin"
datastore_password = "admin"

controller_url = "http://selforch.name29.net:8080"
controller_username = "admin"
controller_password = "admin"

configuration_url = "http://selforch.name29.net:8082"
configuration_username = "admin"
configuration_password = "admin"

#
# try:
#     conf = Configuration('config/default-config.ini')
# except Exception as e:
#     logging.error("Unable to load configuration: "+e.message);
#     quit(1)

# set log level
# if conf.DEBUG is True:
#     log_level = logging.DEBUG
#     requests_log = logging.getLogger("requests")
#     requests_log.setLevel(logging.WARNING)
# elif conf.VERBOSE is True:
#     log_level = logging.INFO
#     requests_log = logging.getLogger("requests")
#     requests_log.setLevel(logging.WARNING)
# else:
#     log_level = logging.WARNING

log_level = logging.DEBUG
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

# format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'

#logging.basicConfig(filename=conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.basicConfig(filename="file.log", level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug("Service Orchestrator Starting")
print("Welcome to the User-oriented Service Orchestrator Application")
logging.info("Starting Service Orchestrator application")

# start the dd client to receive information about domains
#base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
#dd_client = DDClient(conf.DD_NAME, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
#thread = Thread(target=dd_client.start)
#thread.start()

datastore = DatastoreClient(base_url=datastore_url,
                            username=datastore_username,
                            password=datastore_password)
configuration_service = ConfigurationService(username=configuration_username,
                                             password=configuration_password,
                                             base_url=configuration_url,
                                             timeout=30000)

orchestrator = InfrastructureOrchestrator(username=controller_username,
                                          password=controller_password,
                                          base_url=controller_url,
                                          timeout=30000)

while True:
    command = raw_input("add / remove ? ")

    if command == "add":
        add_host(orchestrator, datastore, nffg_name)
        print "Added!"
    elif command == "remove":
        remove_host(orchestrator, nffg_name)
        print "Removed!"
    elif command == "exit":
        exit(1)
    else:
        print "invalid command"