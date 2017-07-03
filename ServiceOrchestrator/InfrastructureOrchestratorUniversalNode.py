'''
Created on Jun 24, 2015

@author: fabiomignini
'''
import logging
import requests
import json
from NotAuthenticatedException import NotAuthenticatedException
from ConnectionException import ConnectionException
from vnf_template_library.template import Template
from vnf_template_library.validator import ValidateTemplate
from nffg_library.nffg import NF_FG
from nffg_library.validator import ValidateNF_FG


class InfrastructureOrchestratorUniversalNode(object):

    def __init__(self, username , password , host, port, timeout):
        self.timeout = timeout
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = "http://" + str(host) + ":" + str(port)
        self.login_url = self.base_url + "/login"
        self.nffg_url = self.base_url + "/NF-FG/%s"
        self.get_status_url = self.base_url + "/NF-FG/status/%s"
        self.get_template = self.base_url + "/template/location/%s"
        self.headers = {
                        'Content-Type': 'application/json',
                        'cache-control': 'no-cache'
                        }
        self.authenticate()

    def authenticate(self):
        self.headers = {
                        'Content-Type': 'application/json',
                        'cache-control': 'no-cache'
                        }

        try:
            r = requests.post(self.login_url,
                          headers=self.headers,
                          data = json.dumps({"username": self.username, "password": self.password}),
                          timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (r.status_code == 200):
            self.headers = {
                                'Content-Type': 'application/json',
                                'cache-control': 'no-cache',
                                'X-Auth-Token': r.text
                            }
        else:
            raise Exception("UniversalNode: Unable to login " + str(r.status_code))

    def getNFFGStatus(self,nffg_id):
        try:
            self._getNFFGStatus(nffg_id)
        except NotAuthenticatedException as ex:
            self._authenticate()
            self._getNFFGStatus(nffg_id)

    def getNFFG(self, nffg_id):
        try:
            _getNFFG(nffg_id)
        except NotAuthenticatedException as ex:
            _authenticate()
            _getNFFG(nffg_id)

    def addNFFG(self, nffg):
        try:
            self._addNFFG(nffg)
        except NotAuthenticatedException as ex:
            self._authenticate()
            self._addNFFG(nffg)

    def removeNFFG(self, nffg_id):
        try:
            self._removeNFFG(nffg_id)
        except NotAuthenticatedException as ex:
            self._authenticate()
            self._removeNFFG(nffg_id)

    def getTemplate(self, vnf_template_location):
        raise NotImplementedError("getTemplate not implemented for UniversalNode")

    def _getNFFGStatus(self, nffg_id):
        try:
            resp = requests.get(self.get_status_url % (nffg_id), headers=self.headers, timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)
        logging.debug("HTTP response status code: " + str(resp.status_code))
        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")
        resp.raise_for_status()
        logging.debug("Check completed")
        # dict_resp = ast.literal_eval(resp.text)
        return resp.text

    def _getNFFG(self, nffg_id):
        try:
            resp = requests.get(self.get_nffg_url % (nffg_id), headers=self.headers, timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")

        resp.raise_for_status()
        nffg_dict = json.loads(resp.text)
        ValidateNF_FG().validate(nffg_dict)
        nffg = NF_FG()
        nffg.parseDict(nffg_dict)
        logging.debug("Get NFFG completed")
        return nffg

    def _addNFFG(self, nffg):
        try:
            data= nffg.getJSON(domain=True)
            data = data.replace('IPv4','ipv4')
            resp = requests.put(self.nffg_url % (nffg.name), data=data, headers=self.headers,
                            timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")
        resp.raise_for_status()
        logging.debug("Put completed")
        return resp.text

    def _deleteNFFG(self, nffg_id):
        try:
            resp = requests.delete(self.nffg_url % (nffg_id), headers=self.headers, timeout=int(self.timeout))
        except Exception as e :
            raise ConnectionException(e.message)

        if (resp.status_code == 401):
            raise NotAuthenticatedException("Not authenticated")
        resp.raise_for_status()
        logging.debug("Delete completed")
        return resp.text