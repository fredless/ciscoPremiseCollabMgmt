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
import re
import csv
import io

# leverages SSH workers in VOS modules
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
        
    def sql (self, sql, db='unitydirdb'):
        """ Execute CLI SQL query and return result. Common DB unitydirdb is default but can be overridden """

        return(api.vos.ssh.send_command(self.cucvos, self.cucshell, f'run cuc dbquery {db} {sql}'))

    def sqlcsv(self, sql, db='unitydirdb'):
        """ Execute CLI SQL query and return results as CSV.  Common DB unitydirdb is default but can be overridden """

        result = api.vos.ssh.send_command(self.cucvos, self.cucshell, f'run cuc dbquery {db} {sql}').splitlines()
        # should find column breaks in first 2-3l of fixed width result
        for line in result[:3]:
                # unity sql query column break row uses '-' char
                if line[:1] == "-":
                    separator_found = True
                    # ..and column headers are separated by double spaces
                    column_breaks = [cseparator.start() for cseparator in re.finditer('  ', line)]
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
            for column_break in column_breaks:
                slices.append(slice(offset, column_break))
                offset = column_break + 2
            # add slice for the last column
            slices.append(slice(offset,len(line)))
        
        # parse result into csv
        result_csv = io.StringIO()
        csv_writer = csv.writer(result_csv)
        for line in result:
            if line[:2] != "--":
                csv_writer.writerow([line[slice].strip() for slice in slices])
        return (result_csv.getvalue())
