
import logging
import requests
import json
import NotAuthenticatedException
import ConnectionException
from ConfigurationSDN import ConfigurationSDN

class ConfigurationService(object):

    def __init__(self, username, password, host, port, timeout):
        self.timeout = timeout
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = "http://" + str(host) + ":" + str(port)+"/config"
        self.get_config_url = self.base_url + "/status/%s/%s/%s"
        self.put_config_url = self.base_url + "/vnf/%s/%s/%s"

        self.headers = {
                        'Content-Type': 'application/json',
                        'cache-control': 'no-cache'
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

    def getConfiguration(self,tenant_id,nffg_id,vnf_id):
        try:
            return self._getConfiguration(tenant_id,nffg_id,vnf_id)
        except NotAuthenticatedException as ex:
            self._authenticate()
            self._getConfiguration(tenant_id,nffg_id,vnf_id)

    def setConfiguration(self, configuration):
        try:
            self._setConfiguration(configuration.tenant_id, configuration.nffg_id, configuration.vnf_id,configuration)
        except NotAuthenticatedException as ex:
            self._authenticate()
            self._setConfiguration(configuration.tenant_id, configuration.nffg_id, configuration.vnf_id,configuration)

    def removeConfiguration(self, configuration):
        #TODO
        pass

    def _getConfiguration(self,tenant_id,nffg_id,vnf_id):
        try:
            resp = requests.get(self.get_config_url % (vnf_id,nffg_id,tenant_id), headers=self.headers, timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")

        conf = ConfigurationSDN(tenant_id, nffg_id, vnf_id)

        if (resp.status_code == 404):
            #Nessuna configuratione trovata nel config. service. Ritorno una cfg vuota
            print conf
            return conf

        resp.raise_for_status()

        config_dict = json.loads(resp.text)
        conf.parseDict(config_dict)
        logging.debug("Get Configuration completed")
        return conf

    def _setConfiguration(self,tenant_id,nffg_id,vnf_id,configuration):
        try:
            data = configuration.getJSON()
            print data

            resp = requests.put(self.put_config_url % (vnf_id,nffg_id,tenant_id), data=data, headers=self.headers,
                            timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")
        resp.raise_for_status()
        logging.debug("Put configuration completed")
        return resp.text
