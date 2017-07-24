

from ConfigurationSDN import ConfigurationSDN
import datetime
import time
import ipaddress
import logging

class NatMonitor(object):

    def __init__(self, configuration_service, on_nat_fault, on_new_host, on_left_host, timeout_left_ms=10000, polling_time_ms=1000):
        self.on_new_host = on_new_host
        self.on_left_host = on_left_host
        self.timeout_left_ms = timeout_left_ms
        self.polling_time_ms = polling_time_ms
        self.configuration_service = configuration_service
        self.on_nat_fault = on_nat_fault
        self.nats = []

    def addNat(self,tenant_id, nffg_id, vnf_id):
        ret = dict()
        ret["tenant_id"]=tenant_id
        ret["nffg_id"]=nffg_id
        ret["vnf_id"]=vnf_id
        ret["active_hosts"]=dict()

        logging.debug("New NAT monitored: %s" % ret)
        self.nats.append(ret)

    def removeNat(self,vnf_id):
        for nat in self.nats:
            if vnf_id == nat["vnf_id"]:
                logging.warning("Removed the NAT with id %s " % vnf_id)
                self.nats.remove(nat)
                return

        logging.warning("Unable to remove the NAT: the id %s is not inside the list" % vnf_id)

    def run(self,lan_network):
        while True:
            logging.debug("New iteration started")
            new_hosts = []
            left_hosts = []

            for nat in self.nats:
                logging.debug("Checking the NAT VNF with id %s" % nat["vnf_id"])

                try:
                    cfg = self.configuration_service.getConfiguration(nat["tenant_id"],nat["nffg_id"],nat["vnf_id"])
                except Exception as e:
                    logging.error("Unable to read the configuration of %s: %s" %(nat,e))
                    self.on_nat_fault(nat)
                    continue

                arp_table = dict()

                if "config-nat:nat" in cfg.configuration and "arp-table" in cfg.configuration["config-nat:nat"] and "arp-entry" in cfg.configuration["config-nat:nat"]["arp-table"]:
                    for arp_entry in cfg.configuration["config-nat:nat"]["arp-table"]["arp-entry"]:
                        logging.debug("Adding ARP entry %s -> %s (NAT %s)" % (arp_entry["ip_address"], arp_entry["mac_address"], nat["vnf_id"]))
                        arp_table[arp_entry["ip_address"]] = arp_entry["mac_address"]
                else:
                    logging.warning("config-nat:nat -> arp-table -> arp-entry is not found inside the configuration of NAT %s" % nat["vnf_id"])

                if "config-nat:nat" in cfg.configuration and "nat-table" in cfg.configuration["config-nat:nat"] and "nat-session" in cfg.configuration["config-nat:nat"]["nat-table"]:
                    for session in cfg.configuration["config-nat:nat"]["nat-table"]["nat-session"]:
                        host = session["src_address"]
                        logging.debug("Found nat-session with src-address %s on the NAT %s" % (host,nat["vnf_id"]))

                        if host not in nat["active_hosts"].keys():
                            logging.info("The host %s is new (found in nat-session on NAT %s)" % (host, nat["vnf_id"]))
                            if ipaddress.ip_address(host) in ipaddress.ip_network(lan_network):
                                logging.info("The host %s is inside the lan_network %s (found in one nat-session on NAT '%s')" % (host,lan_network, nat["vnf_id"]))

                                d = dict()
                                d["ip"]=host
                                d["mac-address"] = "00:00:00:00:00:00"
                                if host in arp_table.keys():
                                    d["mac-address"] = arp_table[host]
                                else:
                                    logging.error("Unable to find mac-address of the ip %s -> %s (NAT %s) using %s" %(host,arp_table,nat["vnf_id"],d["mac-address"]))

                                d["last-seen"] = datetime.datetime.now()
                                nat["active_hosts"][host] = d

                                new_hosts.append(d)

                        nat["active_hosts"][host]["last-seen"] = datetime.datetime.now()

                    for host in nat["active_hosts"].keys():
                        expire_date = nat["active_hosts"][host]["last-seen"] + datetime.timedelta(milliseconds=self.timeout_left_ms)
                        if expire_date < datetime.datetime.now():
                            logging.info("The host %s is expired (NAT %s) " % (host,  nat["vnf_id"]))

                            left_hosts.append(nat["active_hosts"][host])
                            nat["active_hosts"].pop(host)

            for new_host in new_hosts:
                logging.debug("Notifying the new host '%s' " % new_host)
                self.on_new_host(new_host)

            for left_host in left_hosts:
                logging.debug("Notifying the expired host '%s' " % new_host)
                self.on_left_host(left_host)

            time.sleep(self.polling_time_ms/1000.0)



