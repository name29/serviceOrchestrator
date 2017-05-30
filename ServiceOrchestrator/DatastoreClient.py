import requests
import logging
from  vnf_template_library.template import Template
import json

class DatastoreClient:
	def __init__(self,base_URL):
		self.base_URL=base_URL+'/v2/'
		self.headers={"Accept":'application/json','Content-type':'application/json'}
		self.timeout=1000

	#def get_template(self, vnf_id):
	#	url = self.base_URL+'nf_template/'+image_id
	#	return get(url)

	def delete_template(self,image_id):
		url = self.base_URL+'nf_template/'+image_id+'/'
		return delete(url)

	def delete_image(self, image_id):
		url = self.base_URL+'nf_image/'+image_id+'/'
		return delete(url)

	def put_template(self,image_id,manifestJSON):
		url=self.base_URL+'nf_template/'+image_id+'/'
		return put(url,data=manifestJSON, headers=self.headers)

	def get_template_json(self,template_name):
		resp = requests.get(self.base_URL + 'nf_template/%s' % (template_name), headers=self.headers, timeout=int(self.timeout))
		logging.debug("HTTP response status code: " + str(resp.status_code))
		resp.raise_for_status()
		logging.debug("Check completed")
		# dict_resp = ast.literal_eval(resp.text)
		return resp.text

	def getTemplate(self,template_name):
		template_json = self.get_template_json(template_name)
		template_dict = json.loads(template_json)
		ta = Template()
		ta.parseDict(template_dict)

		return ta
