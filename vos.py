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

import sys
from time import time, sleep

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
                index1 = output.find('\n')
                index2 = output.rfind('\n')
                return output[index1+1:index2]
        
        # if loop ends before CLI prompt is seen, assume failure
        return {'fault': f"{self.prompt_timeout}{self.msg_timerexp}{self.msg_commandcompl}"}   




              


     
