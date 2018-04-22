# Copyright (C) 2018 Frederick W. Nielsen
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
    Implements simplistic Serviceability Control Center POST.  Used to activate or deactivate services in VOS.
    """

    def __init__(self, userid, pw, nodeip, nodename, timeout=10, cert_verify=False):
        """ Initiate a new CC client instance """
        
        self.auth=requests.auth.HTTPBasicAuth(userid, pw)
        self.nodeip = nodeip
        self.nodename = nodename
        self.timeout = timeout
        
        # establish XML namespaces used later to construct and parse requests
        self.ns0 = "http://schemas.xmlsoap.org/soap/envelope/"
        self.ns1 = "http://schemas.cisco.com/ast/soap"
        
        # suppress certificate advice
        if not cert_verify:
           urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.cert_verify = cert_verify


    def cc_cucm_envelope(self, nodename, action, services):
        """ SOAP envelope string builder """
        
        # mandatory SOAP envelope and namespaces
        envelope = "<?xml version='1.0' encoding='utf8'?>" +\
                   f"<soapenv:Envelope xmlns:soapenv=\"{self.ns0}\" xmlns:soap=\"{self.ns1}\">" 
        
        # omit optional SOAP header, placeholder
        ### envelope += '<ns0:Header/>'
        
        # construct opening body
        envelope += "<soapenv:Body><soap:soapDoServiceDeployment><soap:DeploymentServiceRequest>"

        # add node name, not sure if CUCM validates this or not, but required
        envelope += f"<soap:NodeName>{nodename}</soap:NodeName>"
        
        # specify deployment type, Deploy to activate, UnDeploy to deactivate
        envelope += f"<soap:DeployType>{action}</soap:DeployType>"

        # added services to deploy
        envelope += "<soap:ServiceList>"
        for each in services:
            envelope += f"<soap:item>{each}</soap:item>"
        envelope += "</soap:ServiceList>"
        
        # close tags
        envelope += "</soap:DeploymentServiceRequest></soap:soapDoServiceDeployment>"
        envelope += "</soapenv:Body></soapenv:Envelope>"

        return envelope


    