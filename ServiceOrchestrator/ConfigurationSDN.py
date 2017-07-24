
#TODO
class ConfigurationSDN(object):

    def __init__(self,tenant_id, nffg_id, vnf_id):
        self.tenant_id = tenant_id
        self.nffg_id = nffg_id
        self.vnf_id = vnf_id
        self.configuration = dict()


        self.lan_ip=""
        self.lan_mac=""
        self.wan_ip=""
        self.wan_gw=""
        self.man_ip=""

    def parseDict(self, d):
        self.configuration = dict(d)

    def get(self,what,where):
        if ( what == "ip"):
            if ( where == 'WAN:0'):
                if "config-nat:interfaces" in self.configuration.keys() and "ifEntry" in self.configuration["config-nat:interfaces"].keys():
                    for iface in self.configuration["config-nat:interfaces"]["ifEntry"]:
                        if iface["id"] == where:
                            address = dict()
                            address["ip"] = iface["ipv4_configuration"]["address"]
                            address["netmask"] = iface["ipv4_configuration"]["netmask"]

                            return address
                else:
                    raise Exception("Actual configuration does not contains interfaces information")
        raise Exception("Invalid parameters")

    def getJSON(self):
        return """       
         {
            "config-nat:interfaces": {
                "ifEntry": [{
                        "id": "WAN:0",
                        "name": "eth0",
                        "type": "L3",
                        "ipv4_configuration": {
                            "address": "%s",
                            "netmask": "255.255.255.0",
                            "default_gw": "%s",
                            "configurationType": "static"
                        },
                        "management": false
                    },
                    {
                        "id": "LAN:1",
                        "name": "eth1",
                        "type": "L3",
                        "ipv4_configuration": {
                            "address": "%s",
                            "netmask": "255.255.255.0",
                            "mac_address": "%s",
                            "configurationType": "static"
                        },
                        "management": false
                    }
                ]
            },
            "config-nat:nat": {
                "public-interface": "WAN:0",
                "private-interface": "LAN:1",
                "floatingIP": []
            }
        }
        """ % ( self.wan_ip, self.wan_gw, self.lan_ip ,self.lan_mac)

    def setIP(self,port,ip,netmask,gateway=None,mac_address=None):

        if ( "User" in port):
            self.lan_ip = ip
            self.lan_mac = mac_address
            return
        if ( "WAN" in port):
            self.wan_ip = ip
            self.wan_gw = gateway
            return
#        if ( "MAN" in port):
#            self.man_ip = ip

        print "ERRORE!!!?!??!"