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

import api.vos

class ssh:
    """
    Implements several CLI work methods for CUC platforms.
    """

    def __init__(self, userid, pw, nodeip, prompt='admin:', prompt_timeout=60, key_verify=False):
        """ Initiate a new SSH client instance """
        
        self.userid = userid
        self.pw = pw
        self.nodeip = nodeip
        self.prompt = prompt
        self.prompt_timeout = prompt_timeout
        self.key_verify = key_verify
        self.cucvos = api.vos.ssh(userid, pw, nodeip)
        self.cucshell = self.cucvos.connect_interactive()
        
    def sql (self, sql, db="unitydirdb"):
        """ Execute CLI SQL query and return result as string. Common DB unitydirdb is default but can be overridden """

        return(api.vos.ssh.send_command(self.cucvos, self.cucshell, f'run cuc dbquery {db} {sql}'),'\n')
