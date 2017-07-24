from SelfOrchestratingNatService import SelfOrchestratingNatService
import logging
import sys


log_level = logging.INFO
#log_level = logging.DEBUG
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

log_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)s:%(funcName)s() - %(message)s'

if False:
    logging.basicConfig(filename="file.log", level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
else:
    logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')


sons = SelfOrchestratingNatService()
sons.run()






