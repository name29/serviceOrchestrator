
from nffg_library.nffg import NF_FG, VNF, Port,EndPoint,FlowRule,Match,Action
import logging

class LoadBalancerL2(object):

    def __init__(self, nffg, mac, port_in, default_port):
        self.mac = mac
        self.port_in = port_in
        self.counter = 0;

        self.set_default(nffg,default_port)

    def set_default(self,nffg, out_port):
        flowrules = nffg.getFlowRulesStartingWith("LB_DEFAULT_")
        for flowrule in flowrules:
            logging.debug("removing flow rule with name '%s'  " % (flowrule.id))
            nffg.removeFlowRule(flowrule.id)

        logging.debug("setting default flow rule : port_in=%s -> %s " %(self.port_in,out_port))

        nffg.addFlowRule(
            FlowRule("LB_DEFAULT_"+str(self.counter), 1, Match(port_in=self.port_in), [Action(out_port)]))

        logging.debug("setting reply flow rule : port_in=%s -> %s " %(out_port,self.port_in))

        nffg.addFlowRule(
            FlowRule("LB_REPLY_"+str(self.counter), 2, Match(port_in=out_port), [Action(self.port_in)]))
        self.counter = self.counter + 1

    def get_default_port(self, nffg):
        flowrules = nffg.getFlowRulesStartingWith("LB_DEFAULT")

        if len(flowrules) > 0 :
            flow_rule = flowrules[0]
            d = flow_rule.getDict()
            ret = d["actions"][0]["output_to_port"]
            logging.info("default output port  %s " % (ret))
            return ret
        else:
            logging.error("unable to find the default flow rules with prefix LB_DEFAULT %s" % (nffg.flow_rules))
            raise Exception("Unable to find LB_DEFAULT_X flowrule")

    def get_port_host(self,nffg,host_mac):
        flow_rule_name = "LB_"+host_mac.replace(":","")
        flow_rule = nffg.getFlowRule(flow_rule_name)

        if flow_rule is None:
            logging.error("Unable to find flow rule with name %s" % (flow_rule_name))
            raise Exception("Unable to find flow rule with name %s" % (flow_rule_name))

        d = flow_rule.getDict()
        ret = d["actions"][0]["output_to_port"]

        logging.debug("output port for host %s : %s " %(host_mac,ret))

        return ret

    def remove_host(self, nffg, host_mac):
        flow_rule_name="LB_"+host_mac.replace(":","")
        logging.debug("removing flow rule %s " %(flow_rule_name))

        flow_rule = nffg.getFlowRule(flow_rule_name)

        if flow_rule is None:
            logging.warning("no flow rule with name %s exists" %(flow_rule_name))
            return

        nffg.removeFlowRule(flow_rule_name)

    def exist_balance(selfs, nffg, host_mac):
        flow_rule_name = "LB_" + host_mac.replace(":", "")

        flow_rule = nffg.getFlowRule(flow_rule_name)

        if flow_rule is not None:
            logging.error("Already exist a load-balancing rule for source_mac=%s!" % (host_mac))
            return True
        return False

    def add_balance(self, nffg, host_mac, out_port):

        flow_rule_name = "LB_" + host_mac.replace(":", "")

        logging.info("setting flow rule : port_in=%s,source_mac=%s,dest_mac=%s -> %s " %(self.port_in,host_mac,self.mac,out_port))

        if self.exist_balance(nffg,host_mac):
            raise Exception("Already exist a load-balancing rule for source_mac=%s!" % host_mac)

        nffg.addFlowRule(
            FlowRule(flow_rule_name, 2, Match(port_in=self.port_in,source_mac=host_mac,dest_mac=self.mac), [Action(out_port)]))

    def get_mac_host_to_vnf(self,nffg,vnf_id):
        flowrules = nffg.getFlowRulesStartingWith("LB_")

        for flow_rule in flowrules:
            d = flow_rule.getDict()
            port = d["actions"][0]["output_to_port"]

            if port.split(":")[1] == vnf_id:
                if "match" in d.keys():
                    if "source_mac" in d["match"].keys():
                        print d["match"]["source_mac"]
        return None

    def dump(self, nffg):
        flowrules = nffg.getFlowRulesStartingWith("LB_")

        for flowrule in flowrules:
            print flowrule.getDict()
