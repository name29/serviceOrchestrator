
import logging
import requests
import json
import time
import NotAuthenticatedException
import ConnectionException
from ConfigurationSDN import ConfigurationSDN

class ConfigurationService(object):

    def __init__(self, username, password, base_url, timeout):
        self.timeout = timeout
        self.username = username
        self.password = password
        self.base_url = base_url
        self.get_config_url = self.base_url + "/config/%s/%s/%s/"
        self.put_config_url = self.base_url + "/config/%s/%s/%s/"
        self.get_started_url = self.base_url + "/config/started_vnf"

        self.headers = {
                        'content-type': 'application/json'
                        }
        self.authenticate()

    def authenticate(self):
        return True

        # self.headers = {
        #                 'Content-Type': 'application/json',
        #                 'cache-control': 'no-cache'
        #                 }
        #
        # try:
        #     r = requests.post(self.login_url,
        #                   headers=self.headers,
        #                   data = json.dumps({"username": self.username, "password": self.password}),
        #                   timeout=int(self.timeout))
        # except Exception as e :
        #     raise ConnectionException(e.message)
        #
        # if (r.status_code == 200):
        #     self.headers = {
        #                         'Content-Type': 'application/json',
        #                         'cache-control': 'no-cache',
        #                         'X-Auth-Token': r.text
        #                     }
        # else:
        #     raise Exception("UniversalNode: Unable to login " + str(r.status_code))

    def getConfiguration(self, tenant_id, nffg_id, vnf_id):
        try:
            return self._getConfiguration(tenant_id, nffg_id, vnf_id)
        except NotAuthenticatedException:
            self._authenticate()
            self._getConfiguration(tenant_id, nffg_id, vnf_id)

    def setConfiguration(self, configuration):
        try:
            self._setConfiguration(configuration.tenant_id, configuration.nffg_id, configuration.vnf_id,configuration)
        except NotAuthenticatedException:
            self._authenticate()
            self._setConfiguration(configuration.tenant_id, configuration.nffg_id, configuration.vnf_id,configuration)

    def getStartedVNF(self):
        try:
            return self._getStartedVNF()
        except NotAuthenticatedException:
            self._authenticate()
            return self._getStartedVNF()

    def removeConfiguration(self, tenant_id, nffg_id, vnf_id):
        #TODO
        pass

    def _getConfiguration(self,tenant_id,nffg_id,vnf_id):
        while True:
            try:
                logging.debug("Trying to get the configuration of %s/%s/%s" % (tenant_id, nffg_id, vnf_id))
                resp = requests.get(self.get_config_url % (tenant_id, nffg_id, vnf_id), headers=self.headers, timeout=int(self.timeout))
            except Exception as e:
                logging.error("Exception during the get of the configuration of %s/%s/%s: %s" % (tenant_id, nffg_id, vnf_id, e))
                raise Exception(e)

            if resp.status_code == 401:
                logging.info("Authentication needed during the get of the configuration of  %s " % (tenant_id, nffg_id, vnf_id))
                raise NotAuthenticatedException("Not authenticated")

            logging.debug("get of the configuration of %s/%s/%s completed with HTTP status code %s" % (tenant_id, nffg_id, vnf_id, resp.status_code))

#           if resp.status_code != 500:
#               break

#           logging.debug("get of the configuration of %s/%s/%s returned HTTP status code 500, try again " % (tenant_id, nffg_id, vnf_id))
#          time.sleep(1)
            break

        conf = ConfigurationSDN(tenant_id, nffg_id, vnf_id)

        if resp.status_code == 404:
            logging.info("No configuration found for %s/%s/%s, returing empty configuration" % (tenant_id, nffg_id, vnf_id))
            return conf

        resp.raise_for_status()

        config_dict = json.loads(resp.text)
        conf.parseDict(config_dict)
        return conf

    def _getStartedVNF(self):
        try:

            logging.debug("Trying to get the running VNF")
            resp = requests.get(self.get_started_url, headers=self.headers,
                                timeout=int(self.timeout))
        except Exception as e:
            logging.error("Exception during the get of running VNF : %s" % e)
            raise ConnectionException(e.message)

        if resp.status_code == 401:
            logging.info("Authentication needed during the get of running VNF")
            raise NotAuthenticatedException("Not authenticated")

        logging.debug("Get of running VNF returned HTTP status code %s" % resp.status_code)

        resp.raise_for_status()
        started_list = json.loads(resp.text)
        return started_list

    def waitUntilStarted(self,tenant_id,nffg_id,vnf_id):
        while True:
            started_list = self.getStartedVNF()

            logging.debug("Is %s/%s/%s started ? Running VNF: %s" % (tenant_id, nffg_id, vnf_id, started_list))
            for started in started_list:
                if started["graph_id"] == nffg_id and started["vnf_id"]== vnf_id and started["tenant_id"] == tenant_id :
                    logging.debug("%s/%s/%s is started!" % (tenant_id, nffg_id, vnf_id))
                    return True

            logging.debug("%s/%s/%s is NOT started! =( " % (tenant_id, nffg_id, vnf_id))
            time.sleep(1)

    def _setConfiguration(self,tenant_id,nffg_id,vnf_id,configuration):
        while True:
            try:
                data = configuration.getJSON()

                logging.debug("Trying to put a new configuration for %s/%s/%s " % (tenant_id, nffg_id, vnf_id))

                resp = requests.put(self.put_config_url % (tenant_id,nffg_id,vnf_id), data=data, headers=self.headers,
                                    timeout=int(self.timeout))
            except Exception as e:
                logging.error("Exception during the put of the new VNF %s/%s/%s" % (tenant_id, nffg_id, vnf_id))
                raise Exception(e)

            logging.debug("Put of the new configuration for %s/%s/%s completed with HTTP status %s" % (tenant_id, nffg_id, vnf_id, resp.status_code))

            if resp.status_code == 401:
                logging.info("Authentication needed during the put of the configuration for %s/%s/%s" % (tenant_id, nffg_id, vnf_id))
                raise NotAuthenticatedException("Not authenticated")

            if resp.status_code != 500:
                break

            logging.debug("Put of the configuration for %s/%s/%s returned HTTP status code 500, try again " % (tenant_id, nffg_id, vnf_id))
            time.sleep(1)

        resp.raise_for_status()
        return resp.text
