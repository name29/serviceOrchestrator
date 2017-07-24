from SelfOrchestratingNatService import SelfOrchestratingNatService
import logging
import sys
from ServiceOrchestrator.ConfigurationSDN import ConfigurationSDN
from ServiceOrchestrator.ConfigurationService import ConfigurationService
from ServiceOrchestrator.InfrastructureOrchestrator import InfrastructureOrchestrator


log_level = logging.DEBUG
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

log_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)s:%(funcName)s() - %(message)s'

if False:
    logging.basicConfig(filename="file.log", level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
else:
    logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

configuration_url = "http://selforch.name29.net:8082"
configuration_username = "admin"
configuration_password = "admin"

controller_url = "http://selforch.name29.net:8080"
controller_username = "admin"
controller_password = "admin"

orchestrator = InfrastructureOrchestrator(username=controller_username,
                                               password=controller_password,
                                               base_url=controller_url,
                                               timeout=30000)
nffg_name="test_nffg_nat"
try:
    nffg = orchestrator.getNFFG(nffg_name)
except Exception as ex:
    logging.error("Unable to get NFFG with name %s : %s " % (nffg_name, ex))
    exit(1)

nffg.removeVNF("NAT_8S82")

try:
    orchestrator.addNFFG(nffg)
except Exception as ex:
    logging.error("Error during the add of the NFFG with name %s" % ex)
    exit(1)