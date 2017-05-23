#!/usr/bin/env python

import requests


class UniversalNode:
	base_url = ""
	username = ""
	password = ""
	auth_token = ""

	def __init__(self,server,port,username,password):
		self.base_url = "http://"+server+":"+port

		pass

	def getAuthenticationToken(self):
		r = requests.post(base_url+"/login", { "username": self.username , "password" : self.password)

		if ( r.status_code == 200 ):
			self.auth_token = r.text
		else:
			raise Exception("UniversalNode: Unable to login "+str(r.status_code))


	def putGraph(self,graph):

	def getGraph(self,graph_name):

	def statusGraph(self,graph_name):

X-AUTH-TOKEN
PUT /NF-FG/mioGraph
GET /NF-FG/mioGraph
GET /NF-FG/status/mioGraph


