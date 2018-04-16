# Copyright (C) 2018 Frederick w. Nielsen
# 
# This file is part of Cisco On-Premise Collab API Management Routines.
# 
# Cisco On-Premise Collab API Management Routines is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Cisco On-Premise Collab API Management Routines is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Cisco On-Premise Collab API Management Routines.  If not, see <http://www.gnu.org/licenses/>.

import sys
import dicttoxml
import xmltodict
import urllib3

import requests

class server:
    """
    Implements simplistic AXL POST.  Rather than bundling big WSDL files that also take significant time to 
    process, we build AXL requests from scratch.
    """

    def __init__(self, userid, pw, nodeip, axlversion, timeout=10, cert_verify=False):
        """ Initiate a new AXL client instance """
        
        self.auth=requests.auth.HTTPBasicAuth(userid, pw)
        self.nodeip = nodeip
        self.timeout = timeout
        
        # establish XML namespaces used later to construct and parse requests
        self.ns0 = "http://schemas.xmlsoap.org/soap/envelope/"
        self.ns1 = "http://www.cisco.com/AXL/API/{0}".format(axlversion)
        
        # suppress certificate advice
        if not cert_verify:
           urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.cert_verify = cert_verify


    def axl_cucm_envelope(self, axlnamespace, axlparams):
        """ SOAP envelope string builder """
        
        # mandatory SOAP envelope and namespaces
        envelope = "<?xml version='1.0' encoding='utf8'?>" +\
                   "<ns0:Envelope xmlns:ns0=\"{0}\" xmlns:ns1=\"{1}\">".format(self.ns0,self.ns1) 
        
        # omit optional SOAP header, placeholder
        ### envelope += '<ns0:Header/>'
        
        # construct body, this is where request's namespace is provided
        envelope += "<ns0:Body><ns1:{0} sequence=\"\">".format(axlnamespace)

        # adding parameters from dict converting to xml
        envelope += dicttoxml.dicttoxml(axlparams, attr_type=False, root=False).decode('utf-8')

        # close tags
        envelope += "</ns1:{0}></ns0:Body></ns0:Envelope>".format(axlnamespace)

        return envelope


    def request(self, axlnamespace, axlparams):
        """
        Given the AXL namespace (request type) and a dict with the applicable payload XML, will transact a request 
        and return answer in dict.
        """

        url = "https://{0}:8443/axl/".format(self.nodeip)

        # build the request body
        soapenvelope=self.axl_cucm_envelope(axlnamespace,axlparams)

        # send the request
        try:
            request = requests.post(url, data=soapenvelope, auth=self.auth, verify=self.cert_verify,
                      timeout=self.timeout)
            # catch for various HTTP errors
            if request.status_code == 599:
                # custom error when API doesn't support schema version provided
                return {'fault': "Error (<class 'requests.exceptions.HTTPError'>, "
                "HTTPError('599 Server Error: issue with AXL subsystem or version specified',))"}
            elif request.status_code >= 400:
                request.raise_for_status()
        except:
            return {'fault': "Error {0}".format(sys.exc_info()[:2])}
        
        # parse response into dict and output parts
        request_dict = xmltodict.parse(request.text, process_namespaces=True)
        body_dict = request_dict['{0}:Envelope'.format(self.ns0)]['{0}:Body'.format(self.ns0)]

        # look for errors
        if '{0}:{1}Response'.format(self.ns1, axlnamespace) in body_dict:
            return body_dict['{0}:{1}Response'.format(self.ns1, axlnamespace)]
        elif '{0}:Fault'.format(self.ns0) in body_dict:
            return {'fault': body_dict['{0}:Fault'.format(self.ns0)]}
        else:
            return body_dict
    