# Copyright (C) 2018 Frederick W. Nielsen
# 
# This file is part of Cisco On-Premise Collab API Management Routines.
# 
# Cisco On-Premise Collab API Management Routines is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
# 
# Cisco On-Premise Collab API Management Routines is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with 
# Cisco On-Premise Collab API Management Routines.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys

import dicttoxml
import requests
import urllib3 
import xmltodict


class axl:
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
        self.ns1 = f"http://www.cisco.com/AXL/API/{axlversion}"
        
        # suppress certificate advice
        if not cert_verify:
           urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.cert_verify = cert_verify


    def envelope(self, axlnamespace, axlparams):
        """ SOAP envelope string builder """
        
        # mandatory SOAP envelope and namespaces
        envelope = "<?xml version='1.0' encoding='utf8'?>" +\
                   f"<ns0:Envelope xmlns:ns0=\"{self.ns0}\" xmlns:ns1=\"{self.ns1}\">" 
        
        # omit optional SOAP header, placeholder
        ### envelope += '<ns0:Header/>'
        
        # construct body, this is where request's namespace is provided
        envelope += f"<ns0:Body><ns1:{axlnamespace} sequence=\"\">"

        # adding parameters from dict converting to xml
        envelope += dicttoxml.dicttoxml(axlparams, attr_type=False, root=False).decode('utf-8')

        # close tags
        envelope += f"</ns1:{axlnamespace}></ns0:Body></ns0:Envelope>"

        return envelope


    def request(self, axlnamespace, axlparams):
        """
        Given the AXL namespace (request type) and a dict with the applicable payload XML, will transact a request 
        and return answer in dict.
        """

        if not axlnamespace or not axlparams:
            return {'fault': "missing axlnamespace or axlparams"}            

        url = f"https://{self.nodeip}:8443/axl/"

        # build the request body
        soapenvelope=self.envelope(axlnamespace,axlparams)

        # send the request
        try:
            request = requests.post(url, data=soapenvelope, auth=self.auth, verify=self.cert_verify,
                      timeout=self.timeout)
            # catch for various HTTP errors
            if request.status_code == 599:
                # custom error when API doesn't support schema version provided
                return {'xmldata': soapenvelope, 'fault': "Error (<class 'requests.exceptions.HTTPError'>, "
                "HTTPError('599 Server Error: issue with AXL subsystem or version specified',))"}
            elif request.status_code >= 400:
                request.raise_for_status()
        except:
            return {'xmldata': soapenvelope, 'fault': f"Error {sys.exc_info()[:2]}"}
        
        # parse response into dict and output parts
        request_dict = xmltodict.parse(request.text, process_namespaces=True)
        body_dict = request_dict[f'{self.ns0}:Envelope'][f'{self.ns0}:Body']

        # look for errors
        if f'{self.ns1}:{axlnamespace}Response' in body_dict:
            return body_dict[f'{self.ns1}:{axlnamespace}Response']
        elif f'{self.ns0}:Fault' in body_dict:
            return {'xmldata': soapenvelope, 'fault': body_dict[f'{self.ns0}:Fault']}
        else:
            return body_dict

    def sqlquery(self, sql):
        """ Shortcut for executing read-only AXL SQL requests """

        if not sql:
            return {'fault': "missing SQL query"}  
        return (self.request('executeSQLQuery', {'sql': f'{sql}'}))

    def sqlupdate(self, sql):
        """ 
        Shortcut for executing write AXL SQL requests 
        ### USE WITH CAUTION, a single misconstructed SQL update statement can take down
        a production system! ###
        """

        if not sql:
            return {'fault': "missing SQL query"}  
        return (self.request('executeSQLUpdate', {'sql': f'{sql}'}))


class controlcenter:
    """
    Implements simplistic Serviceability Control Center POST.  Used to activate or deactivate services in VOS.
    """

    def __init__(self, userid, pw, nodeip, nodename, timeout=300, cert_verify=False):
        """ Initiate a new CC client instance """
        
        self.auth=requests.auth.HTTPBasicAuth(userid, pw)
        self.nodeip = nodeip
        self.nodename = nodename
        self.timeout = timeout
        
        # establish XML namespaces and elements used later to construct and parse requests
        self.ns0 = "http://schemas.xmlsoap.org/soap/envelope/"
        self.ns1 = "http://schemas.cisco.com/ast/soap"
        self.element1 = "soapDoServiceDeployment"
        self.element2 = "DeploymentServiceRequest"
        
        # suppress certificate advice
        if not cert_verify:
           urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.cert_verify = cert_verify


    def expand_shortcuts (self, services):
        """ expands list of predefined service shortcut names """

        shortcuts = {
                    'axl': "Cisco AXL Web Service",
                    'bulk': "Cisco Bulk Provisioning Service",
                    'capf': "Cisco Certificate Authority Proxy Function",
                    'car': "Cisco CAR Web Service",
                    'cm': "Cisco CallManager",
                    'cti': "Cisco CTIManager",
                    'ctl': "Cisco CTL Provider",
                    'dirsync': "Cisco DirSync",
                    'dna': "Cisco Dialed Number Analyzer",
                    'dnaserver': "Cisco Dialed Number Analyzer Server",
                    'em': "Cisco Extension Mobility",
                    'extfunc': "Cisco Extended Functions",
                    'ils': "Cisco Intercluster Lookup Service",
                    'ipma': "Cisco IP Manager Assistant",
                    'lbm': "Cisco Location Bandwidth Manager",
                    'media': "Cisco IP Voice Media Streaming App",
                    'selfprovision': "Self Provisioning IVR",
                    'serviceability': "Cisco Serviceability Reporter",
                    'snmp': "Cisco CallManager SNMP Service",
                    'soapcdr': "Cisco SOAP - CDRonDemand Service",
                    'taps': "Cisco TAPS Service",
                    'tftp': "Cisco Tftp",
                    'uxl': "Cisco UXL Web Service",
                    'webdialer': "Cisco WebDialer Web Service"
                    }
        
        # Iterate shortcut list, rewrite service list with substitutions
        for shortcut in shortcuts:
            services = [re.sub(f'^{shortcut}$', shortcuts[shortcut], service, flags=re.IGNORECASE)
                        for service in services]
        return services

    def envelope(self, action, services):
        """ SOAP envelope string builder """
        
        # mandatory SOAP envelope and namespaces
        envelope = "<?xml version='1.0' encoding='utf8'?>" +\
                   f"<soapenv:Envelope xmlns:soapenv=\"{self.ns0}\" xmlns:soap=\"{self.ns1}\">" 
        
        # omit optional SOAP header, placeholder
        ### envelope += '<ns0:Header/>'
        
        # construct opening body
        envelope += f"<soapenv:Body><soap:{self.element1}><soap:{self.element2}>"

        # add node name, not sure if CUCM validates this or not, but required
        envelope += f"<soap:NodeName>{self.nodename}</soap:NodeName>"
        
        # specify deployment type, Deploy to activate, UnDeploy to deactivate
        envelope += f"<soap:DeployType>{action}</soap:DeployType>"

        # add services to deploy
        services = self.expand_shortcuts(services) 
        envelope += "<soap:ServiceList>"
        for service in services:
            envelope += f"<soap:item>{service}</soap:item>"
        envelope += "</soap:ServiceList>"
        
        # close tags
        envelope += f"</soap:{self.element2}></soap:{self.element1}>"
        envelope += "</soapenv:Body></soapenv:Envelope>"

        return envelope

    def clean_response(self, old_dict):
        """ removes namespace from first dictionary part of returned response """

        clean_dict = {}
        for key, value in old_dict.items():
            if isinstance(value, dict):
                value = self.clean_response(value)
            clean_dict[key.replace(f'{self.ns1}:', '')] = value
        return clean_dict


    def request(self, action, services):
        """
        Given the ControlCenter deployment action and a list of services, posts request and returns
        answer in dict.
        """

        if action not in ('Deploy', 'UnDeploy'):
            return {'fault': "action must be specified as either Deploy or UnDeploy"}
        
        if not services:
            return {'fault': "at least one service must be passed as list"}
        
        url = f"https://{self.nodeip}:8443/controlcenterservice2/services/ControlCenterServices/"

        # build the request body
        soapenvelope=self.envelope(action,services)
        
        # send the request
        try:
            request = requests.post(url, data=soapenvelope, auth=self.auth, verify=self.cert_verify,
                      timeout=self.timeout)
            if request.status_code >= 400:
                request.raise_for_status()
        except:
            return {'fault': f"Error {sys.exc_info()[:2]}"}

        
        # parse response into dict and output parts
        request_dict = xmltodict.parse(request.text, process_namespaces=True)
        body_dict = request_dict[f'{self.ns0}:Envelope'][f'{self.ns0}:Body'] \
                    [f'{self.ns1}:{self.element1}Response'] \
                    [f'{self.ns1}:{self.element1}Return']

        body_dict = self.clean_response(body_dict)

        # look for errors 
        if body_dict['ReasonCode'] != "-1":
            return dict(
                {'xmldata': soapenvelope,
                'fault': f"Error: service activation call failed on {self.nodename}"},
                **body_dict
                )
   

        if action == "Deploy":
            failed_list = ''
            if isinstance(body_dict['ServiceInfoList']['item'], list):
                for service in body_dict['ServiceInfoList']['item']:
                    if (service[f'{self.ns1}:ReasonCode']) == "-1068":
                        print (str(service[f'{self.ns1}:ServiceName']))
                        failed_list.join(service[f'{self.ns1}:ServiceName'])
            else:
                if body_dict['ServiceInfoList']['item']['ReasonCode'] == "-1068":
                    failed_list = body_dict['ServiceInfoList']['item']['ServiceName']
            if failed_list != '':
                return dict(
                    {'xmldata': soapenvelope,
                    'fault': f"Error: the following services failed to activate: {failed_list}"},
                    **body_dict)
            
        return dict({'xmldata': soapenvelope}, **body_dict)
