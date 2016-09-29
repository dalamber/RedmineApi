"""
The MIT License (MIT)

Copyright (c) [2014] [Anton Shpakovsky]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os, urllib, urllib2, json, traceback
from datetime import date

"""
=== config file example ===
{
	"redmine_url"	: "http://redmine.mycompany.com/myproject",
	"project_id"	: "website",
	"passkey"		: "abc3e131dwsdff234sd12334zxc234"
}
"""

class Redmine():
	# Initialize from input parameters (url/project/passkey)
	def __init__(self, url, project, passkey):
		self.__setup(url, project, passkey)		

	# Initialize from config file
	@classmethod
	def fromConfigFile(cls, config):
		try:
			with open(config, 'r') as f:
				json_config = json.loads(f.read())
				url     = json_config['redmine_url']
				project = json_config['project_id']
				config  = json_config['passkey']
				return cls(url, project, config)				
		except Exception as e:
			print traceback.format_exc(e)
	
	# Returns json containing information about all project versions
	def versions(self):
		request = self.redmine_url + '/projects/%s/versions.json' % self.project
		return urllib2.urlopen(request).read()

	def setVersionDescription(self, version, description):
		self.__changeVersionDescription(version, description)

	# Create new version
	def addVersion(self, version):
		headers = {'Content-type': 'application/json'};
		data  = json.dumps({ 
			'version' : {'name' : version}
			})
		req = urllib2.Request(self.redmine_url + '/projects/%s/versions.json' % self.project, data, headers)
		urllib2.urlopen(req).read()

	# Lock existing version
	def lockVersion(self, version):
		self.__changeVersionStatus(version, 'locked')

	# Reopen 'locked' or 'closed' version
	def openVersion(self, version):
		self.__changeVersionStatus(version, 'open')

	# Close version
	def closeVersion(self, version):
		self.__changeVersionStatus(version, 'closed')

	# Returns all issues assigned to the given 'version'
	def issues(self, version):
		versionId = self.__versionId(version)
		request_str = self.redmine_url + '/projects/%s/issues.json?fixed_version_id=%s' % (self.project, versionId)
		data = urllib2.urlopen(request_str).read()
		return json.loads(data)['issues']

	# ------------------------------------------
	def __setup(self, url, project, passkey):
		try:
			self.email_cache = {}
			self.redmine_url = url
			self.project  = project
			
			passwordMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
			passwordMgr.add_password(None, self.redmine_url, passkey, '')
			authhandler = urllib2.HTTPBasicAuthHandler(passwordMgr)
			self.opener = urllib2.build_opener(authhandler)
			urllib2.install_opener(self.opener)
		except Exception as e:
			print traceback.format_exc(e)

	def __changeVersionStatus(self, version, status):
		if status not in ['locked', 'open', 'closed']:
			return

		versionId = self.__versionId(version)
		data = json.dumps({
				'version' : { 
				'id' : versionId, 
				'status' : status,
				'effective_date' : str(date.today())
			}})

		headers = {'Content-type': 'application/json'};
		request_str = self.redmine_url + '/versions/%s.json' % (versionId)
		req = urllib2.Request(request_str, data, headers)		
		req.get_method = lambda: 'PUT'
		urllib2.urlopen(req).read()

	def __changeVersionDescription(self, version, description):
		versionId = self.__versionId(version)

		data = json.dumps({
				'version' : { 
				'id' : versionId,
				'description' : description
			}})

		headers = {'Content-type': 'application/json'};
		request_str = self.redmine_url + '/versions/%s.json' % (versionId)
		req = urllib2.Request(request_str, data, headers)		
		req.get_method = lambda: 'PUT'
		urllib2.urlopen(req).read()

	def __versionId(self, version):
		versions = self.versions()
		version_array = json.loads(versions)['versions']
		for v in version_array:
			if v['name'] == version:
				return v['id']

		raise Exception('Version %s was not found!' % version)

if __name__ == "__main__":
	pass