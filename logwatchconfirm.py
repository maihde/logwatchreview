#!/usr/bin/env python
#
# Copyright (C) 2011 Michael Ihde
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import cgi
import ConfigParser

config = ConfigParser.ConfigParser()
config.read(['logwatchreview.cfg', os.path.expanduser('~/.logwatchreview.cfg'), "/etc/logwatchreview.cfg"])
savedir = os.path.expanduser(os.path.expandvars(config.get("logwatchreview", "savedir")))

OK_MESSAGE="""
<html>
  <head>
     <title>Thank You</title>
  </head>
  <body>
      <p>Thank You</p>
  </body>
</html>
"""

ERROR_MESSAGE="""
<html>
  <head>
     <title>Error</title>
  </head>
  <body>
      <h1>Error</h1>
      <p>%s</p>
  </body>
</html>
"""

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

form = cgi.FieldStorage()
if "token" not in form:
    print ERROR_MESSAGE % "No token provided"
    sys.exit(0)
	
token = form["token"].value
outputFile = os.path.join(savedir, "logwatch_%s" % token)
if not os.path.exists(outputFile):
    print ERROR_MESSAGE % "Invalid token"
else:
    try:
        os.unlink(outputFile)
    except OSError, e:
        print ERROR_MESSAGE % str(e)
	sys.exit(0)
print OK_MESSAGE
