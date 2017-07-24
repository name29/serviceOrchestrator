# Tutti i nat lato LAN hanno lo stesso ip e lo stesso mac-address

import logging
import requests
import time
import json
import sys
import random
import string

# from ServiceOrchestrator.DDClient import DDClient

from nffg_library.nffg import NF_FG, VNF, Port,EndPoint,FlowRule,Match,Action

from ServiceOrchestrator.ConfigurationSDN import ConfigurationSDN
from ServiceOrchestrator.InfrastructureOrchestrator import InfrastructureOrchestrator
from ServiceOrchestrator.ConnectionException import ConnectionException
from ServiceOrchestrator.DatastoreClient import DatastoreClient
from ServiceOrchestrator.IpPool import IpPool
from ServiceOrchestrator.ConfigurationService import ConfigurationService
from ServiceOrchestrator.LoadBalancer import LoadBalancerL2
from ServiceOrchestrator.NatMonitor import  NatMonitor


class SelfOrchestratingNatService(object):

    def __init__(self):

        self.counter = 1

        self.nffg_id = "1"
        self.nffg_name = "test_nffg_nat"
        self.tenant_id = "2"
        self.nat_mac = "02:01:02:03:04:05"
        self.nat_lan = {"ip": "192.168.10.1", "netmask": "255.255.255.0"}
        self.lan = u'192.168.10.0/24'

        self.random_str = '' + random.choice(string.ascii_uppercase + string.digits) \
                          + random.choice(string.ascii_uppercase + string.digits)\
                          + random.choice(string.ascii_uppercase + string.digits)

        datastore_url = "http://selforch.name29.net:8081"
        datastore_username = "admin"
        datastore_password = "admin"

        controller_url = "http://selforch.name29.net:8080"
        controller_username = "admin"
        controller_password = "admin"

        configuration_url = "http://selforch.name29.net:8082"
        configuration_username = "admin"
        configuration_password = "admin"

        self.ip_pool = IpPool()

        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.100', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.101', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.102', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.103', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.104', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.105', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.106', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.107', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.108', '255.255.255.0')
        self.ip_pool.add_ip_in_pool('WAN', '192.168.11.109', '255.255.255.0')

        logging.debug("Service Orchestrator Starting(Log)")

        # start the dd client to receive information about domains
        # base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
        # dd_client = DDClient(conf.DD_NAME, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
        # thread = Thread(target=dd_client.start)
        # thread.start()

        logging.info("Connecting to the datastore")
        self.datastore = DatastoreClient(username=datastore_username,
                                         password=datastore_password,
                                         base_url=datastore_url)

        logging.info("Connecting to the configuration service")
        self.configuration_service = ConfigurationService(username=configuration_username,
                                                          password=configuration_password,
                                                          base_url=configuration_url,
                                                          timeout=10)

        logging.info("Connecting to the infrastructure orchestrator")
        self.orchestrator = InfrastructureOrchestrator(username=controller_username,
                                                       password=controller_password,
                                                       base_url=controller_url,
                                                       timeout=30000)

        logging.info("Removing old NFFG with name '%s' " % self.nffg_name)

        try:
            self.orchestrator.removeNFFG(self.nffg_name)
        except Exception:
            pass

        logging.debug("Getting template from the datastore")

        self.template_nat = self.datastore.getTemplate("nat")
        template_switch = self.datastore.getTemplate("switch")
        # template_orch = self.datastore.getTemplate("serviceorch")
        template_dhcpserver = self.datastore.getTemplate("dhcpserver")
        template_dhcpserver_man = self.datastore.getTemplate("dhcpserverman")

        logging.debug("Building the VNFs")

        nat_vnf =self.buildVNF(self.template_nat,"NAT"+self.random_str, "NAT"+self.random_str)
        dhcpserver_vnf =self.buildVNF(template_dhcpserver,"DHCPLAN", "DHCPLAN")
        dhcpserver_man_vnf =self.buildVNF(template_dhcpserver_man,"DHCPMAN", "DHCPMAN")

        self.switch_man_vnf =self.buildVNF(template_switch,"SWITCH_MAN", "SWITCH_MAN")
        self.switch_lan_vnf =self.buildVNF(template_switch,"SWITCH_LAN", "SWITCH_LAN")
        self.switch_wan_vnf =self.buildVNF(template_switch,"SWITCH_WAN", "SWITCH_WAN")

        # orch_vnf =self.buildVNF(template_orch,"SELFORCH","serviceorch")

        management_endpoint = EndPoint("MANAGEMENT_ENDPOINT", "MANAGEMENT_ENDPOINT", "host-stack",
                                       configuration="static", ipv4="192.168.40.1/24")
        internet_endpoint = EndPoint("INTERNET_ENDPOINT", "INTERNET_ENDPOINT", "host-stack", configuration="static",
                                     ipv4="192.168.11.1/24")

        logging.debug("Creating the NFFG")
        deploy_nffg = NF_FG(self.nffg_id, self.nffg_name)

        logging.debug("Adding VNF to NFFG")

        # deploy_nffg.addVNF(orch_vnf)
        deploy_nffg.addVNF(nat_vnf)
        deploy_nffg.addVNF(dhcpserver_vnf)
        deploy_nffg.addVNF(dhcpserver_man_vnf)
        deploy_nffg.addVNF(self.switch_man_vnf)
        deploy_nffg.addVNF(self.switch_lan_vnf)
        deploy_nffg.addVNF(self.switch_wan_vnf)
        deploy_nffg.addEndPoint(management_endpoint)
        deploy_nffg.addEndPoint(internet_endpoint)

        logging.debug("Creating link between VNF")

        # Connect SWITCH_MAN to DHCP MAN
        self.link_ports(deploy_nffg,
                        "DHCP_SWITCH_MAN",
                        "SWITCH_MAN_DHCP",
                        dhcpserver_man_vnf.getFullnamePortByLabel("inout"),
                        self.switch_man_vnf.getFullnamePortByLabel(self.switch_man_vnf.getFreePort(deploy_nffg, "port")))

        # Connect SWITCH_LAN to DHCP
        self.link_ports(deploy_nffg,
                        "DHCP_SWITCH_LAN",
                        "SWITCH_LAN_DHCP",
                        dhcpserver_vnf.getFullnamePortByLabel("inout"),
                        self.switch_lan_vnf.getFullnamePortByLabel(
                           self.switch_lan_vnf.getFreePort(deploy_nffg, "port")))

        # Connect Switch_WAN to NAT
        self.link_ports(deploy_nffg,
                       "NAT_SWITCH_WAN",
                       "SWITCH_WAN_NAT",
                        nat_vnf.getFullnamePortByLabel("WAN"),
                        self.switch_wan_vnf.getFullnamePortByLabel(self.switch_wan_vnf.getFreePort(deploy_nffg, "port")))
        # Connect Switch_WAN to INTERNET ENDPOINT
        self.link_ports(deploy_nffg,
                       "INTERNET_SWITCH_WAN",
                       "SWITCH_WAN_INTERNET",
                       "endpoint:INTERNET_ENDPOINT",
                        self.switch_wan_vnf.getFullnamePortByLabel(self.switch_wan_vnf.getFreePort(deploy_nffg, "port")))
        # Connect Endpoint management to Switch_MAN
        self.link_ports(deploy_nffg,
                       "SWITCH_MAN_ENDPOINT",
                       "ENDPOINT_SWITCH_MAN",
                        self.switch_man_vnf.getFullnamePortByLabel(self.switch_man_vnf.getFreePort(deploy_nffg, "port")),
                       "endpoint:MANAGEMENT_ENDPOINT")
        # Connect management port of NAT to Switch_MAN
        self.link_ports(deploy_nffg,
                       "SWITCH_MAN_NAT",
                       "NAT_SWITCH_MAN",
                        self.switch_man_vnf.getFullnamePortByLabel(self.switch_man_vnf.getFreePort(deploy_nffg, "port")),
                        nat_vnf.getFullnamePortByLabel("management"))

        # Connect management port of SELFORCH to Switch_MAN
        # linkPorts(deploy_nffg,"SWITCH_MAN_SELFORCH","SELFORCH_SWITCH_MAN",SWITCH_MAN_vnf.getFullnamePortByLabel(SWITCH_MAN_vnf.getFreePort(deploy_nffg,"port")),orch_vnf.getFullnamePortByLabel("inout"))

        logging.debug("Creating LoadBalancer L2")

        self.load_balancer = LoadBalancerL2(nffg=deploy_nffg,
                                            mac=self.nat_mac,
                                            port_in=self.switch_lan_vnf.getFullnamePortByLabel("port2"),
                                            default_port=nat_vnf.getFullnamePortByLabel("User"))

        logging.info("Sending initial NFFG")
        try:
            self.orchestrator.addNFFG(deploy_nffg)
        except Exception as ex:
            logging.error("Error during the add of the NFFG with name %s" % ex)
            exit(1)

        nat_cfg = ConfigurationSDN(self.tenant_id, self.nffg_id, nat_vnf.id)

        logging.debug("Trying to get one ip for the WAN interface from the Pool")
        nat_wan = self.ip_pool.get('WAN')

        if nat_wan is None:
            logging.error("Error during the get of an ip from the pool '%s' : Pool is empty" % nat_wan)
            exit(1)

        logging.info("WAN IP For the NAT '%s' is '%s'" % (nat_vnf.id,nat_wan["ip"]))

        logging.debug("Configuring the nat VNF")

        nat_cfg.setIP(port="User", ip=self.nat_lan['ip'], netmask=self.nat_lan['netmask'], mac_address=self.nat_mac)
        nat_cfg.setIP(port="WAN", ip=nat_wan['ip'], netmask=nat_wan['netmask'], gateway="192.168.11.1")

        logging.info("Trying to put the configuration for the VNF '%s'" % nat_vnf.id)
        try:
            self.configuration_service.waitUntilStarted(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)
            self.configuration_service.setConfiguration(nat_cfg)
        except Exception as ex:
            logging.error("Error during the put of the configuration for '%s' : '%s'" % (nat_vnf.id, ex))
            exit(1)

        logging.debug("Configuring the NatMonitor")

        self.nat_monitor = NatMonitor(self.configuration_service, self.on_nat_fault, self.on_host_new, self.on_host_left)

        logging.debug("Adding the NAT %s in the NatMonitor" % nat_cfg.vnf_id)

        self.nat_monitor.addNat(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)

        logging.info("Waiting for one host")

    def on_nat_fault(self, nat):
        logging.info("The NAT %s does not respond. Removing it from NFFG and re-route traffic (nffg_name=%s)" % (nat["vnf_id"], self.nffg_name))

        self.nat_monitor.removeNat(nat["vnf_id"])
        #TODO Re-route traffic now over nat to default route and add a new nat

        logging.info("Trying to get the NFFG with name '%s'" % self.nffg_name)
        try:
            nffg = self.orchestrator.getNFFG(self.nffg_name)
        except Exception as ex:
            logging.error("Unable to get NFFG with name '%s' : '%s'" % (self.nffg_name, ex))
            exit(1)

        nat_name = nat["vnf_id"]

        mac = self.load_balancer.get_mac_host_to_vnf(nffg,nat_name)

        logging.debug("Mac-address over '%s' is '%s'" % (nat_name,mac))

        if mac is None:
            logging.info("'%s' is the default NAT" % nat_name)

            nffg.removeVNF(nat_name)

            vnf_name = "NAT" + self.random_str + str(self.counter)
            self.counter = self.counter + 1

            vnf_id = vnf_name
            nat_name = vnf_name

            nat_vnf = self.buildVNF(self.template_nat, vnf_id, vnf_name)

            nffg.addVNF(nat_vnf)

            self.load_balancer.set_default(nffg,nat_vnf.getFullnamePortByLabel("User"))

            logging.debug("Trying to get VNF")

            switch_man_vnf = nffg.getVNF("SWITCH_MAN")
            switch_wan_vnf = nffg.getVNF("SWITCH_WAN")

            self.link_ports(nffg,
                            vnf_id + "_SWITCH_WAN", "SWITCH_WAN_" + vnf_id,
                            nat_vnf.getFullnamePortByLabel("WAN"),
                            switch_wan_vnf.getFullnamePortByLabel(switch_wan_vnf.getFreePort(nffg, "port")))
            self.link_ports(nffg,
                            vnf_id + "_SWITCH_MAN", "SWITCH_MAN_" + vnf_id,
                            nat_vnf.getFullnamePortByLabel("management"),
                            switch_man_vnf.getFullnamePortByLabel(switch_man_vnf.getFreePort(nffg, "port")))

            logging.info("Sending the modified NFFG")
            try:
                self.orchestrator.addNFFG(nffg)
            except Exception as ex:
                logging.error("Error during the add of the NFFG with name %s" % ex)
                exit(1)

            nat_cfg = ConfigurationSDN(self.tenant_id, self.nffg_id, nat_vnf.id)

            logging.debug("Trying to get one ip for the WAN interface from the Pool")
            nat_wan = self.ip_pool.get('WAN')

            if nat_wan is None:
                logging.error("Error during the get of an ip from the pool '%s' : Pool is empty" % nat_wan)
                exit(1)

            logging.info("WAN IP For the NAT '%s' is '%s'" % (nat_vnf.id,nat_wan["ip"]))

            logging.debug("Configuring the nat VNF")

            nat_cfg.setIP(port="User", ip=self.nat_lan['ip'], netmask=self.nat_lan['netmask'], mac_address=self.nat_mac)
            nat_cfg.setIP(port="WAN", ip=nat_wan['ip'], netmask=nat_wan['netmask'], gateway="192.168.11.1")

            logging.info("Trying to put the configuration for the VNF '%s'" % nat_vnf.id)
            try:
                self.configuration_service.waitUntilStarted(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)
                self.configuration_service.setConfiguration(nat_cfg)
            except Exception as ex:
                logging.error("Error during the put of the configuration for '%s' : '%s'" % (nat_vnf.id, ex))
                exit(1)

            logging.debug("Adding the NAT %s in the NatMonitor" % nat_cfg.vnf_id)

            self.nat_monitor.addNat(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)

            logging.info("Waiting for host")
        else:
            logging.info("Remove and add again host with Mac-Address '%s'" % mac)

            host = dict()
            host["ip"] = "X.Z.Y.K"
            host["mac-address"] = mac

            logging.debug("Configuring the LoadBalancer")
            self.load_balancer.remove_host(nffg, mac)

            logging.debug("Removing the VNF with name '%s'" % nat_name)
            nffg.removeVNF(nat_name)

            return self.on_host_new(host, nffg)

    def on_host_new(self, host, nffg=None):

        logging.info("New host found '%s' -> '%s' (nffg_name=%s)" % (host["ip"], host["mac-address"], self.nffg_name))

        if nffg is None:
            logging.info("Trying to get the NFFG with name '%s'" % self.nffg_name)
            try:
                nffg = self.orchestrator.getNFFG(self.nffg_name)
            except Exception as ex:
                logging.error("Unable to get NFFG with name '%s' : '%s'" % (self.nffg_name,ex))
                exit(1)

            if self.load_balancer.exist_balance(nffg,host["mac-address"]):
                logging.error("Already exist a load-balance rule for '%s'" % host["mac-address"])
                return True


        logging.debug("Trying to get VNF")

        switch_man_vnf = nffg.getVNF("SWITCH_MAN")
        switch_wan_vnf = nffg.getVNF("SWITCH_WAN")

        # BUG, l'ON non accetta vnf_name lunghi
        # vnf_name="NAT_"+nat_wan['ip'].replace(".","_")

        vnf_name = "NAT"+self.random_str+str(self.counter)
        self.counter = self.counter + 1

        vnf_id = vnf_name
        nat_vnf =self.buildVNF(self.template_nat,vnf_id ,vnf_name)

        nffg.addVNF(nat_vnf)

        logging.debug("Add link for the new VNF")

        self.link_ports(nffg,
                        vnf_id + "_SWITCH_WAN", "SWITCH_WAN_" + vnf_id,
                        nat_vnf.getFullnamePortByLabel("WAN"),
                        switch_wan_vnf.getFullnamePortByLabel(switch_wan_vnf.getFreePort(nffg, "port")))
        self.link_ports(nffg,
                        vnf_id + "_SWITCH_MAN", "SWITCH_MAN_" + vnf_id,
                        nat_vnf.getFullnamePortByLabel("management"),
                        switch_man_vnf.getFullnamePortByLabel(switch_man_vnf.getFreePort(nffg, "port")))

        nat_wan = self.ip_pool.get('WAN')

        if nat_wan is None:
            logging.error("Error during the get of an ip from the pool '%s' : Pool is empty" % nat_wan)
            exit(1)

        logging.info("WAN IP For the NAT '%s' is '%s'" % (nat_vnf.id,nat_wan["ip"]))

        logging.debug("Configuring the NAT VNF '%s'" % nat_vnf.id)

        nat_cfg = ConfigurationSDN(self.tenant_id, self.nffg_id, nat_vnf.id)

        nat_cfg.setIP(port="User", ip=self.nat_lan['ip'], netmask=self.nat_lan['netmask'],mac_address=self.nat_mac)
        nat_cfg.setIP(port="WAN", ip=nat_wan['ip'], netmask=nat_wan['netmask'], gateway="192.168.11.1")

        logging.debug("Updating the LoadBalancer configuration")
        self.load_balancer.add_balance(nffg=nffg,
                                       host_mac=host["mac-address"],
                                       out_port=self.load_balancer.get_default_port(nffg))

        self.load_balancer.set_default(nffg=nffg,
                                       out_port=nat_vnf.getFullnamePortByLabel("User"))

        logging.info("Sending updated NFFG")
        try:
            self.orchestrator.addNFFG(nffg)
        except Exception as ex:
            logging.error("Error during the add of the NFFG:  '%s'" % ex)
            exit(1)

        logging.info("Trying to put the configuration for the VNF '%s'" % nat_vnf.id)

        try:
            self.configuration_service.waitUntilStarted(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)
            self.configuration_service.setConfiguration(nat_cfg)
        except Exception as ex:
            logging.error("Error during the put of the configuration for '%s':'%s'" % (nat_vnf.id, ex))
            exit(1)

        logging.info("Adding the NAT '%s' in the NatMonitor" % nat_cfg.vnf_id)
        self.nat_monitor.addNat(self.tenant_id, self.nffg_id, nat_cfg.vnf_id)

        logging.info("New host found '%s': '%s' (nffg_name='%s') : MANAGED" % (host["ip"], host["mac-address"], self.nffg_name))

        logging.info("Waiting for one host")

        return True

    def on_host_left(self, host):

        logging.info("The host %s (%s) is left " % (host["ip"], host["mac-address"]))

        logging.info("Trying to get the NFFG with name '%s'" % self.nffg_name)
        try:
            nffg = self.orchestrator.getNFFG(self.nffg_name)
        except Exception as ex:
            logging.error("Unable to get NFFG with name '%s' : '%s'" % (self.nffg_name,ex))
            exit(1)

        logging.debug("Configuring the LoadBalancer")
        port = self.load_balancer.get_port_host(nffg,host["mac-address"])
        self.load_balancer.remove_host(nffg, host["mac-address"])

        default_port = self.load_balancer.get_default_port(nffg)
        if port == default_port:
            logging.info("Unable to remove the VNF associated with port '%s', is the last NAT VNF" % port)
            return True

        nat_name = port.split(":")[1]

        logging.debug("Getting the VNF with name '%s'" % nat_name)
        nat_vnf = nffg.getVNF(nat_name)

        logging.info("Getting the configuration of VNF with name '%s'" % nat_name)
        nat_cfg = self.configuration_service.getConfiguration(tenant_id=self.tenant_id, nffg_id=self.nffg_id, vnf_id=nat_vnf.id)
        ip_net_nat_wan = nat_cfg.get('ip', 'WAN:0')
        logging.debug("Freeing the ip %s (WAN ip address of %s)" % (ip_net_nat_wan,nat_name))
        self.ip_pool.free(name='WAN',address=ip_net_nat_wan)

        logging.debug("Removing the VNF with name '%s'" % nat_name)
        nffg.removeVNF(nat_vnf.id)

        logging.info("Sending updated NFFG")
        try:
            self.orchestrator.addNFFG(nffg)
        except Exception as ex:
            logging.error("Error during the add of the NFFG:  '%s'" % ex)
            exit(1)

        logging.info("Trying to remove the configuration for the VNF '%s'" % nat_vnf.id)

        try:
            self.configuration_service.removeConfiguration(tenant_id=self.tenant_id, nffg_id=self.nffg_id, vnf_id=nat_vnf.id)
        except Exception as ex:
            logging.error("Error during the remove of the configuration for  '%s' : '%s'" % (nat_vnf.id, ex))
            exit(1)

        logging.debug("Removing from NAT monitoring the VNF '%s'" % nat_cfg.vnf_id)
        self.nat_monitor.removeNat(nat_cfg.vnf_id)

        logging.info("The host '%s' ('%s') is left: MANAGED" % (host["ip"], host["mac-address"]))

        logging.info("Waiting for one host")
        return True

    def run(self):
        logging.debug("Starting the NatMonitor on %s" % self.lan)
        self.nat_monitor.run(self.lan)
        
        
    def buildVNF(self,template,vnf_id,vnf_name):
        vnf_ports = []
        for port in template.ports:
            port_range = port.position.split('-')
            if port_range[1] == 'N':
                raise Exception("Unable to generate port")

            i_from = int(port_range[0])
            i_to = int(port_range[1])
            for portId in range(i_from , i_to+1):
                vnf_ports.append(Port(port.label+':'+str(portId-1)))

        vnf_id = vnf_id
        vnf = VNF(_id=vnf_id, name=vnf_name,vnf_template_location=template.name,ports=vnf_ports)
        return vnf
     
    def on_host_left_fake(self,host):
        pass

    def disconnect_port(self, nffg, portid):
        if not nffg.existPort(portid):
            raise Exception("Port with id:"+portid+" is invalid")
        nffg.deleteIncomingFlowrules(portid)
        nffg.deleteOutcomingFlowrules(portid)

    def link_ports(self, nffg, flowid1, flowid2, port1, port2):
        if not nffg.existPort(port1):
            raise Exception("Port with id:"+port1+" is invalid")

        if not nffg.existPort(port2):
            raise Exception("Port with id:"+port2+" is invalid")

        nffg.addFlowRule(FlowRule(flowid1, 1, Match(port1), [Action(port2)]))
        nffg.addFlowRule(FlowRule(flowid2, 1, Match(port2), [Action(port1)]))

