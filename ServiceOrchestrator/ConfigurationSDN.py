
#TODO
class ConfigurationSDN(object):

    def __init__(self,tenant_id, nffg_id, vnf_id):
        self.tenant_id = tenant_id
        self.nffg_id = nffg_id
        self.vnf_id = vnf_id
        self.configuration = dict()


        self.lan_ip=""
        self.wan_ip=""
        self.man_ip=""
        self.man_gw=""

    def parseDict(self, d):
        self.configuration = dict(d)

    def getJSON(self):
        return """       
        {
            "config-nat:interfaces": {
                "ifEntry": [
                    {
                        "name": "eth0",
                        "ipv4_configuration": {
                            "configurationType": "static",
                                    "address": "%s"
                        }
                    },
                    {
                        "name": "eth1",
                        "ipv4_configuration": {
                            "configurationType": "static",
                            "address": "%s"
                        }
                    },
                    {
                        "name": "eth2",
                        "managment" : true,
                        "ipv4_configuration": {
                            "configurationType": "static",
                            "address": "%s",
                            "default_gw": "%s"
                        }
                    }
                ]
            },
            "config-nat:nat": {
                "wan-interface": "eth1"
            }
        }
        """ % ( self.lan_ip , self.wan_ip, self.man_ip , self.man_gw)

    def setIP(self,port,ip,netmask,gateway=None,mac_address=None):

        if ( "User" in port):
            self.lan_ip = ip
            return
        if ( "WAN" in port):
            self.wan_ip = ip
            return
        if ( "MAN" in port):
            self.man_ip = ip
            self.man_gw = gateway

        print "ERRORE!!!?!??!"