
from nffg_library.nffg import NF_FG, VNF, Port,EndPoint,FlowRule,Match,Action


class LoadBalancerL2(object):

    def __init__(self, nffg, mac, default_port):
        self.mac = mac

        nffg.addFlowRule(
            FlowRule("LB_DEFAULT", 2, Match(), [Action(default_port)]))


    def set_default(self,nffg, out_port):
        flow_rule = nffg.getFlowRule("LB_DEFAULT")

        d = flow_rule.getDict()
        d["actions"][0]["output_to_port"] = out_port


    def get_default_port(self, nffg):
        flow_rule = nffg.getFlowRule("LB_DEFAULT")

        d = flow_rule.getDict()
        return d["actions"][0]["output_to_port"]

    def get_port_host(self,nffg,host_ip):
        flow_rule = nffg.getFlowRule("LB_"+host_ip)

        d = flow_rule.getDict()
        return d["actions"][0]["output_to_port"]

    def remove_host(self,nffg,host_ip):
        nffg.removeFlowRule("LB_"+host_ip)

    def add_balance(self, nffg, host_ip, out_port):
        nffg.addFlowRule(
            FlowRule("LB_"+host_ip, 1, Match(source_ip=host_ip,dest_mac=self.mac), [Action(out_port)]))



