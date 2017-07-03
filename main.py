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
from ServiceOrchestrator.InfrastructureOrchestratorUniversalNode import InfrastructureOrchestratorUniversalNode
from ServiceOrchestrator.ConnectionException import ConnectionException
from ServiceOrchestrator.DatastoreClient import DatastoreClient
from ServiceOrchestrator.IpPool import IpPool
from ServiceOrchestrator.ConfigurationService import ConfigurationService
from ServiceOrchestrator.LoadBalancer import LoadBalancerL2

def on_host_new(orchestrator, configuration_service, load_balancer, template_nat, switch_lan_vnf,switch_wan_vnf, switch_man_vnf, nffg_name, ip_nat_lan , ip_host, ip_pool):

    try:
        nffg = orchestrator.getNFFG(nffg_name)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    nat_wan = ip_pool.get('WAN')

    if nat_wan is None :
        print "Pool WAN is empty"
        #TODO
        return None

    vnf_name="NAT_"+nat_wan['ip']
    vnf_id = vnf_name

    nat_vnf = template_nat.getVNF(vnf_id,vnf_name)

    nffg.addVNF(nat_vnf)

    linkPorts(nffg, vnf_id+"_SWITCH_LAN", "SWITCH_LAN_"+vnf_id, nat_vnf.getFullnamePortByLabel("User"), switch_lan_vnf.getFullnamePortByLabel(switch_lan_vnf.getFreePort(nffg)))
    linkPorts(nffg, vnf_id+"_SWITCH_WAN", "SWITCH_WAN_"+vnf_id, nat_vnf.getFullnamePortByLabel("WAN"), switch_wan_vnf.getFullnamePortByLabel(switch_wan_vnf.getFreePort(nffg)))
    linkPorts(nffg, vnf_id+"_SWITCH_MAN", "SWITCH_MAN_"+vnf_id, nat_vnf.getFullnamePortByLabel("MAN"), switch_man_vnf.getFullnamePortByLabel(switch_man_vnf.getFreePort(nffg)))

    nat_cfg = configuration_service.getConfiguration(tenant_id=tenant_id, nffg_id=deploy_nffg.id, vnf_id=nat_vnf.id)

    nat_cfg.setIP(port="User:1", ip=nat_lan['ip'], netmask=nat_lan['netmask'])
    nat_cfg.setIP(port="WAN:1", ip=nat_wan['ip'], netmask=nat_wan['netmask'])

    load_balancer.add_balance(nffg=nffg, src_ip=ip_host, out_port=load_balancer.get_default_port())
    load_balancer.set_default(nffg=nffg,out_port=nat_vnf.getFullnamePortByLabel("User"))

    try:
        orchestrator.addNFFG(nffg)
    except ConnectionException as ex:
        print ex.message
        return None
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return None

    try:
        configuration_service.setConfiguration(nat_cfg)
    except ConnectionException as ex:
        print ex.message
        return None
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return None

    return True


def on_host_left(orchestrator, configuration_service, nffg_name, load_balancer, ip_host, ip_pool):

    try:
        nffg = orchestrator.loadNFFG(nffg_name)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    port = load_balancer.get_port_host(nffg,ip_host)

    load_balancer.remove_host(nffg, ip_host)

    if ( port == load_balancer.get_default_port() ):
        #Ultimo Nat, non posso rimuoverlo
        print "Ultimo NAT, non posso rimuoverlo"
        return True

    nat_name = port.split(":")[1]

    nat_vnf = nffg.getVNF(nat_name)

    nat_cfg = configuration_service.getConfiguration(tenant_id=tenant_id, nffg_id=deploy_nffg.id, vnf_id=nat_vnf.id)

    ip_net_nat_wan = nat_cfg.get('ip','WAN:0')

    ip_pool.free(ip_net_nat_wan,'WAN')

    nffg.removeVNF(nat_vnf)

    try:
        configuration_service.setConfiguration(nat_cfg)
    except ConnectionException as ex:
        print ex.message
        return None
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return None

    try:
        orchestrator.addNFFG(nffg)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    try:
        configuration_service.removeConfiguration(nat_cfg)
    except ConnectionException as ex:
        print ex.message
        return False
    except requests.exceptions.HTTPError as ex:
        print ex.message
        return False

    return True


def disconnectPort(nffg, portId):
    if not deploy_nffg.existPort(portId) :
        raise Exception("Port with id:"+portId+" is invalid")
    deploy_nffg.deleteIncomingFlowrules(portId)
    deploy_nffg.deleteOutcomingFlowrules(portId)

def linkPorts(nffg, flowId1, flowId2, port1, port2):
    if  not deploy_nffg.existPort(port1) :
        raise Exception("Port with id:"+port1+" is invalid")

    if not deploy_nffg.existPort(port2) :
        raise Exception("Port with id:"+port2+" is invalid")

    deploy_nffg.addFlowRule(
        FlowRule(flowId1, 1, Match(port1), [Action(port2)]))
    deploy_nffg.addFlowRule(
        FlowRule(flowId2, 1, Match(port2), [Action(port1)]))

nffg_id = "1"
nffg_name = "test_nffg_nat"
tenant_id = 2
nat_mac = "02:01:02:03:04:05"
nat_lan = { "ip": "192.168.10.1", "netmask":"255.255.255.0" }

datastore_url = "http://selforch.name29.net:8081"
datastore_username = "admin"
datastore_password = "admin"

controller_host = "selforch.name29.net"
controller_port = 8080
controller_username = "admin"
controller_password = "admin"

configuration_host = "selforch.name29.net"
configuration_port = 8082
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

datastore = DatastoreClient(datastore_url)
configuration_service = ConfigurationService(username=configuration_username,
                                             password=configuration_password,
                                             host=configuration_host,
                                             port=configuration_port,
                                             timeout=30000)

orchestrator = InfrastructureOrchestratorUniversalNode(username=controller_username,
                                                       password=controller_password,
                                                       host=controller_host,
                                                       port=controller_port,
                                                       timeout=30000)

pool = IpPool()

pool.add_ip_in_pool('WAN','192.168.11.100','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.101','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.102','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.103','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.104','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.105','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.106','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.107','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.108','255.255.255.0')
pool.add_ip_in_pool('WAN','192.168.11.109','255.255.255.0')

template_host = datastore.getTemplate("host_VNF")
template_nat = datastore.getTemplate("nat")
template_switch = datastore.getTemplate("switch")
template_orch = datastore.getTemplate("serviceorch")

host_vnf = template_host.getVNF("HOST","host_VNF")
server_vnf = template_host.getVNF("SERVER","server")
nat_vnf = template_nat.getVNF("NAT","nat")

SWITCH_MAN_vnf = template_switch.getVNF("SWITCH_MAN","SWITCH_MAN")
SWITCH_LAN_vnf = template_switch.getVNF("SWITCH_LAN","SWITCH_LAN")
SWITCH_WAN_vnf = template_switch.getVNF("SWITCH_WAN","SWITCH_WAN")

orch_vnf = template_orch.getVNF("SELFORCH","serviceorch")

managment_endpoint = EndPoint("MANAGMENT_ENDPOINT","MANAGMENT_ENDPOINT","host-stack",configuration="static",ipv4="192.168.40.1/24")

deploy_nffg = NF_FG(nffg_id,nffg_name)

deploy_nffg.addVNF(host_vnf)
deploy_nffg.addVNF(server_vnf)
deploy_nffg.addVNF(orch_vnf)
deploy_nffg.addVNF(nat_vnf)
deploy_nffg.addVNF(SWITCH_MAN_vnf)
deploy_nffg.addVNF(SWITCH_LAN_vnf)
deploy_nffg.addVNF(SWITCH_WAN_vnf)
deploy_nffg.addEndPoint(managment_endpoint)

#Connect SWITCH_LAN to Host
linkPorts(deploy_nffg,"HOST_SWITCH_LAN","SWITCH_LAN_HOST",host_vnf.getFullnamePortByLabel("inout"),SWITCH_LAN_vnf.getFullnamePortByLabel("port1"))
#Connect SWITCH_LAN to NAT
linkPorts(deploy_nffg,"NAT_SWITCH_LAN","SWITCH_LAN_NAT",nat_vnf.getFullnamePortByLabel("User"),SWITCH_LAN_vnf.getFullnamePortByLabel("port2"))
#Connect Switch_WAN to NAT
linkPorts(deploy_nffg,"NAT_SWITCH_WAN","SWITCH_WAN_NAT",nat_vnf.getFullnamePortByLabel("WAN"),SWITCH_WAN_vnf.getFullnamePortByLabel("port2"))
#Connect Switch_WAN to SERVER
linkPorts(deploy_nffg,"SERVER_SWITCH_WAN","SWITCH_WAN_SERVER",server_vnf.getFullnamePortByLabel("inout"),SWITCH_WAN_vnf.getFullnamePortByLabel("port1"))
#Connect Endpoint managment to Switch_MAN
linkPorts(deploy_nffg,"SWITCH_MAN_ENDPOINT","ENDPOINT_SWITCH_MAN",SWITCH_MAN_vnf.getFullnamePortByLabel("port1"),"endpoint:MANAGMENT_ENDPOINT")
#Connect managment port of NAT to Switch_MAN
linkPorts(deploy_nffg,"SWITCH_MAN_NAT","NAT_SWITCH_MAN",SWITCH_MAN_vnf.getFullnamePortByLabel("port2"),nat_vnf.getFullnamePortByLabel("management"))
#Connect managment port of SELFORCH to Switch_MAN
linkPorts(deploy_nffg,"SWITCH_MAN_SELFORCH","SELFORCH_SWITCH_MAN",SWITCH_MAN_vnf.getFullnamePortByLabel("port3"),orch_vnf.getFullnamePortByLabel("inout"))

try:
    orchestrator.addNFFG(deploy_nffg)
except ConnectionException as ex:
    print ex.message
    exit(1)
except requests.exceptions.HTTPError as ex:
    print ex.message
    exit(1)

nat_cfg = configuration_service.getConfiguration(tenant_id=tenant_id, nffg_id=deploy_nffg.id, vnf_id=nat_vnf.id)

print nat_cfg
nat_wan = pool.get('WAN')

if nat_wan is None:
    print "Pool WAN is empty"
    # TODO
    exit(2)

nat_cfg.setIP(port="User", ip=nat_lan['ip'], netmask=nat_lan['netmask'])
nat_cfg.setIP(port="WAN", ip=nat_wan['ip'], netmask=nat_wan['netmask'])


load_balancer = LoadBalancerL2(deploy_nffg,nat_mac,nat_vnf.getFullnamePortByLabel("User"))

try:
    configuration_service.setConfiguration(nat_cfg)
except ConnectionException as ex:
    print ex.message
    exit(1)
except requests.exceptions.HTTPError as ex:
    print ex.message
    exit(1)


on_host_new(orchestrator, configuration_service, load_balancer, template_nat, SWITCH_LAN_vnf,SWITCH_WAN_vnf, SWITCH_MAN_vnf, nffg_name, nat_lan , '192.168.10.100', pool)

exit(1)







