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

import csv
import io
import re
import sys
from time import sleep, time

import paramiko


class ssh:
    """
    Implements several CLI access methods for VOS platforms.
    """

    def __init__(self, userid, pw, nodeip, prompt='admin:', prompt_timeout=60, key_verify=False):
        """ Initiate a new SSH client instance """
        
        self.userid = userid
        self.pw = pw
        self.nodeip = nodeip
        self.prompt = prompt
        self.prompt_timeout = prompt_timeout
        self.key_verify = key_verify
        self.shell_width = None
        self.shell_height = None
        self.msg_timerexp = " second timer expired waiting for "
        self.msg_initprompt = "initial CLI prompt"
        self.msg_commandcompl = "command completion"


    def connect_interactive(self):
        """ Establishes SSH connection """

        newssh = paramiko.SSHClient()

        # suppress SSH key warnings
        if not self.key_verify:
            newssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            newssh.set_missing_host_key_policy(paramiko.RejectPolicy())
       
        print (f'connecting to {self.nodeip}...')
        try:
            newssh.connect(self.nodeip, username=self.userid, password=self.pw)
        except:
            return {'fault': f"Error connecting to {self.nodeip}: {sys.exc_info()[:2]}"}   
         
        print (f'connected, waiting max of {self.prompt_timeout} seconds for {self.msg_initprompt}...')

        new_interactive = newssh.invoke_shell()

        init_time = time()
        
        while (time() - init_time) < self.prompt_timeout:
            output = new_interactive.recv(8000).decode('UTF-8')
            if self.prompt in output:
                print (f'prompt detected. ({round(time() - init_time,1)} seconds)')
                return new_interactive
            
        return {'fault': f"{self.prompt_timeout}{self.msg_timerexp}{self.msg_initprompt}"}   

    def send_command(self, interactive_shell, command):
        """ Sends single command to interactive session and returns command output as string """
        
        print (f'sending command "{command}"\n')
        
        interactive_shell.send(f'{command}\n')
        # wait a beat for command echo, otherwise gets split
        sleep(1)

        output = ''
        # loop gathering output until timer expiry
        command_time = time()
        while (time() - command_time) < self.prompt_timeout:
            output += interactive_shell.recv(65000).decode('UTF-8')
            # watch for CLI prompt
            if self.prompt in output:
                #strip first line (command) and last line (CLI prompt)
                if output.find('\r\n\r\n') == -1:
                    index1 = output.find('\n') + 1
                    index2 = output.rfind('\n')
                else:
                    # some unity commands pad extra carriage returns
                    index1 = output.find('\r\n\r\n') + 4
                    index2 = output.rfind('\n') - 3

                # this returns a tuple, output result in 1st position
                return output[index1:index2]
        
        # if loop ends before CLI prompt is seen, assume failure
        return {'fault': f"{self.prompt_timeout}{self.msg_timerexp}{self.msg_commandcompl}"}   


    def sqlslicer (self, partial_result, db):
        """ Builds slice map from separator row found in raw sql output """
                
        for line in partial_result:
                # ccm sql query column break row uses '=' char, cuc uses '-'
                if line[:1] == "=" or line[:1] == "-":
                    separator_found = True
                    # ..and column headers are separated by single (ccm) or double (cuc) spaces
                    column_breaker = ' ' if db == 'ccm' else '  '
                    column_breaks = [cseparator.start() for cseparator in re.finditer(column_breaker, line)]
                    break

        if not separator_found:
            return {'fault': "unable to parse result, no separator line as expected"} 

        # create slice map
        slices = []
        offset = 0
        if not column_breaks:
            # for single column results
            slices.append(slice(offset,len(line)))
        else:
            # for multiple columns
            slices = []
            offset = 0
            increment = 1 if db == 'ccm' else 2
            for column_break in column_breaks:
                slices.append(slice(offset, column_break))
                offset = column_break + increment
            # grab last column for non-ccm db queries 
            if db != 'ccm':
                slices.append(slice(offset,len(line)))
        
        return slices


    def sql (self, interactive_shell, sql, db='ccm', format='csv'):
        """ Sends single command to interactive session and returns command output as string """
    
        if format not in ('raw', 'csv', 'list'):
            return {'fault': "format needs to be one of raw, csv or list"} 
        
        # can use be used for both ccm or cuc databases
        if db != 'ccm':
            query_cmd = f'run cuc dbquery {db}'
        else:
            query_cmd = 'run sql'

        # run the query
        result = self.send_command(interactive_shell, f'{query_cmd} {sql}')

        if format == 'raw':
            return result
        
        # parse results into list 
        result = result.splitlines()
        slices = self.sqlslicer(result[:3], db)
        sqllist = []
        for line in result:
            if line[:1] != "=" and line[:1] != "-":
                sqllist.append([line[slice].strip() for slice in slices])
        if format == 'list':
            return sqllist

        # convert list to csv, last possible output option
        result_csv = io.StringIO()
        csv_writer = csv.writer(result_csv)   
        csv_writer.writerows(sqllist)

        return result_csv.getvalue()