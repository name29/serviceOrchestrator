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


class InfrastructureOrchestrator(object):

    def __init__(self, username, password, base_url, timeout):
        self.timeout = timeout
        self.username = username
        self.password = password
        self.base_url = base_url
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
            logging.debug("Trying authentication on %s as %s",self.base_url,self.username)
            r = requests.post(self.login_url,
                          headers=self.headers,
                          data = json.dumps({"username": self.username, "password": self.password}),
                          timeout=int(self.timeout))

        except Exception as e:
            logging.error("Error during authentication : %s" % e )
            raise ConnectionException(e.message)

        logging.debug("Authentication HTTP status code: %s" % r.status_code)

        if r.status_code == 200:
            self.headers = {
                                'Content-Type': 'application/json',
                                'cache-control': 'no-cache',
                                'X-Auth-Token': r.text
                            }
        else:
            logging.error("Error during authentication, invalid HTTP status code")
            raise Exception("UniversalNode: Unable to login " + str(r.status_code))

    def getNFFGStatus(self,nffg_id):
        try:
            self._getNFFGStatus(nffg_id)
        except NotAuthenticatedException:
            self.authenticate()
            self._getNFFGStatus(nffg_id)

    def getNFFG(self, nffg_id):
        try:
            return self._getNFFG(nffg_id)
        except NotAuthenticatedException:
            self.authenticate()
            return self._getNFFG(nffg_id)

    def addNFFG(self, nffg):
        try:
            self._addNFFG(nffg)
        except NotAuthenticatedException:
            self.authenticate()
            self._addNFFG(nffg)

    def removeNFFG(self, nffg_id):
        try:
            self._removeNFFG(nffg_id)
        except NotAuthenticatedException:
            self.authenticate()
            self._removeNFFG(nffg_id)

    def getTemplate(self, vnf_template_location):
        logging.error("NotImplementedError: getTemplate is not implemented for UniversalNode")
        raise NotImplementedError("getTemplate is not implemented for UniversalNode")

    def _getNFFGStatus(self, nffg_name):
        try:
            logging.debug("Trying to get the status of NFFG with name %s" % nffg_name)
            resp = requests.get(self.get_status_url % nffg_name, headers=self.headers, timeout=int(self.timeout))
        except Exception as e:
            logging.error("Error during get the status of NFFG with name %s : %s" % (nffg_name, e))
            raise ConnectionException(e.message)

        if resp.status_code == 401:
            logging.info("Authentication needed during get the status of NFFG with name %s " % nffg_name)
            raise NotAuthenticatedException("Not authenticated")

        logging.debug("Get of the NFFG status of %s completed with HTTP status code %s" % (nffg_name, resp.status_code))
        resp.raise_for_status()
        # dict_resp = ast.literal_eval(resp.text)
        return resp.text

    def _getNFFG(self, nffg_name):
        try:
            logging.debug("Trying to get the NFFG with name %s" % nffg_name)
            resp = requests.get(self.nffg_url % nffg_name, headers=self.headers, timeout=int(self.timeout))
        except Exception as e :
            logging.error("Error during the get of NFFG with name %s : %s" % (nffg_name, e))
            raise ConnectionException(e.message)

        if resp.status_code == 401:
            logging.info("Authentication needed during the get of NFFG with name %s " % nffg_name)
            raise NotAuthenticatedException("Not authenticated")

        logging.debug("The get of NFFG with name %s completed wit HTTP status %s" % (nffg_name, resp.status_code))
        resp.raise_for_status()

        #FIX Wrong answer from UniversalNode
        data = resp.text.replace('ipv4', 'IPv4')

        nffg_dict = json.loads(data)
        ValidateNF_FG().validate(nffg_dict)
        nffg = NF_FG()
        nffg.parseDict(nffg_dict)
        return nffg

    def _addNFFG(self, nffg):
        try:
            data = nffg.getJSON(domain=True)

            # FIX Wrong request from UniversalNode
            data = data.replace('IPv4','ipv4')

            logging.debug("Trying to add the NFFG with name %s" % nffg.name)
            resp = requests.put(self.nffg_url % nffg.name, data=data, headers=self.headers,
                            timeout=int(self.timeout))
        except Exception as e:
            logging.error("Error during the add of NFFG with name %s : %s" % (nffg.name,e))
            raise ConnectionException(e.message)

        if resp.status_code == 401:
            logging.info("Authentication needed during the add of NFFG with name %s " % nffg.name)
            raise NotAuthenticatedException("Not authenticated")

        logging.debug("Add of NFFG with name %s completed with HTTP status %s" % (nffg.name, resp.status_code))
        resp.raise_for_status()

        return resp.text

    def _removeNFFG(self, nffg_name):
        try:
            logging.debug("Trying to remove the NFFG with name %s" % nffg_name)
            resp = requests.delete(self.nffg_url % nffg_name, headers=self.headers, timeout=int(self.timeout))
        except Exception as e:
            logging.error("Error during the remove of NFFG with name %s : %s" % (nffg_name, e))
            raise ConnectionException(e.message)

        if resp.status_code == 401:
            logging.info("Authentication needed during the remove of NFFG with name %s " % nffg_name)
            raise NotAuthenticatedException("Not authenticated")

        logging.debug("Delete NFFG with name %s completed with HTTP status %s" % (nffg_name, resp.status_code))

        resp.raise_for_status()

        return resp.text
