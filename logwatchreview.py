#!/usr/bin/env python
# vim: sw=4: et
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
"""
Usage: %prog [options]

Reads a logwatch message from the input, saves it to /var/lib/logwatchreview,
attaches a "reviewed" token URL to the message.
"""
import sys
import os
import hashlib
import socket
import ConfigParser
import pwd
import datetime
import subprocess
from email.mime.text import MIMEText
import smtplib
from optparse import OptionParser

#===============================================================================
# Load the defaults from the config files
#===============================================================================
config = ConfigParser.ConfigParser()
config.read(['logwatchreview.cfg', os.path.expanduser('~/.logwatchreview.cfg'), "/etc/logwatchreview.cfg"])

#===============================================================================
# Parse the arguments
#===============================================================================
p = OptionParser(usage=__doc__)
p.add_option("--savedir",
             dest="savedir",
             default=None)
p.add_option("--confirm-baseurl",
             dest="confirm_baseurl", 
             default=None)
p.add_option("--owner",
             dest="owner", 
             default=None)
p.add_option("--mailto",
             type="str",
             action="append",
             dest="mailto",
             default=None,
             help="an email address to receive the message")
p.add_option("--rrfile",
             type="str",
             dest="rrfile",
             default=None,
             help="the file the keeps track of the last address to receive an email")
p.add_option("--subject",
             type="str",
             dest="subject",
             default=None,
             help="the subject to apply to the email")
p.add_option("--mailfrom",
             type="str",
             default=None,
             dest="mailfrom")
p.add_option("--smtp",
             type="str",
             default=None,
             dest="smtp")
opts, args = p.parse_args()

if opts.savedir == None:
    try:
        opts.savedir = os.path.expanduser(os.path.expandvars(config.get("logwatchreview", "savedir")))
    except ConfigParser.NoOptionError:
        opts.savedir = os.curdir

if opts.owner == None:
    try:
        opts.owner = config.get("logwatchreview", "owner")
    except ConfigParser.NoOptionError:
        opts.owner = None
   
if opts.confirm_baseurl == None:
    try:
        opts.confirm_baseurl = os.path.expanduser(os.path.expandvars(config.get("logwatchreview", "confirm_baseurl")))
    except ConfigParser.NoOptionError:
        opts.confirm_baseurl = "http://%s/cgi-bin/logwatchconfirm.py" % (socket.gethostname())

if opts.mailto == None:
    try:
        opts.mailto = [s.strip() for s in config.get("logwatchreview", "mailto").split()]
    except ConfigParser.NoOptionError:
        opts.mailto = []
        
if opts.subject == None:
    try:
        opts.subject = config.get("logwatchreview", "subject")
    except ConfigParser.NoOptionError:
        opts.subject = "Logwatch from %s" % socket.gethostname()
if opts.mailfrom == None:
    try:
        opts.mailfrom = config.get("logwatchreview", "mailfrom")
    except ConfigParser.NoOptionError:
        opts.mailfrom = "%s@%s" % (os.environ["USER"], socket.gethostname())
        
if opts.smtp == None:
    try:
        opts.smtp = config.get("logwatchreview", "smtp")
    except ConfigParser.NoOptionError:
        opts.smtp = None

if opts.rrfile == None:
    try:
        opts.rrfile = os.path.expanduser(os.path.expandvars(config.get("logwatchreview", "rrfile")))
    except ConfigParser.NoOptionError:
        opts.rrfile = None

if len(opts.mailto) == 0:
    p.error("You must provide at least one recipient")
if opts.rrfile == None:
    p.error("No round-robin file provided")
    
#===============================================================================
# Read the message
#===============================================================================
message = sys.stdin.read()

#===============================================================================
# Generate the 'reviewed token' 
#===============================================================================
h = hashlib.sha1()
h.update(message)
token = h.hexdigest()

#===============================================================================
# Append the 'confirm' URL to the message
#===============================================================================
confirm_url = opts.confirm_baseurl + "?token=%s" % (token)
message += "\nPlease confirm that you have reviewed logs:\n%s\n" % confirm_url

#===============================================================================
# Save the message in case we need to regenerate a review message
#===============================================================================
outputFile = os.path.join(opts.savedir, "logwatch_%s" % token)
f = open(outputFile, "w")
f.write(message)
f.close()
if opts.owner != None:
    uid = pwd.getpwnam(opts.owner)[2]
    gid = pwd.getpwnam(opts.owner)[3]
    os.chown(outputFile, uid, gid)

#===============================================================================
# Select the 'lucky' or 'unlucky' recipient
#===============================================================================
recipient = opts.mailto[0] # Pick the first person by default

try:
    db = open(opts.rrfile, "r")
    with db:
        last_recipient = db.readline().strip()
except IOError:
    pass
else:
    if last_recipient != "":
        # Find the last_recipient in the list,
        # if the email list has changed and the last
        # recipient is no longer in the list...the first
        # person is the stuckee
        for i, mt in enumerate(opts.mailto):
            if mt == last_recipient:
                try:
                    recipient = opts.mailto[i+1]
                except IndexError:
                    recipient = opts.mailto[0] # Redundant...but placed here for clarity
                
db = open(opts.rrfile, "w")
with db:
    db.write(recipient)

#===============================================================================
# Construct and send the email message
#===============================================================================
msg = MIMEText(message)
msg['Subject'] = opts.subject
msg['From'] = opts.mailfrom
msg['To'] = recipient

if opts.smtp != None:
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(opts.smtp)
    s.sendmail(msg['From'], [recipient], msg.as_string())
    s.quit()
else:
    sendmail = subprocess.Popen("sendmail -t", shell=True, stdin=subprocess.PIPE)
    sendmail.stdin.write(msg.as_string())
    sendmail.stdin.close()
    sendmail.wait()

#===============================================================================
# Check for unconfirmed messages
#===============================================================================
today = datetime.datetime.now()
for file in os.listdir(opts.savedir):
    # If it looks like a duck and quacks like a duck
    if file.startswith("logwatch_"):
        fpath = os.path.join(opts.savedir, file)
        ctime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
        if (today-ctime) > datetime.timedelta(days=3):
            #===============================================================================
            # Construct and send the email message to everybody
            #===============================================================================
            message = open(fpath).read()
            msg = MIMEText(message)
            msg['Subject'] = "RESEND " + opts.subject
            msg['From'] = opts.mailfrom
            msg['To'] = ", ".join(opts.mailto)

            if opts.smtp != None:
                # Send the message via our own SMTP server, but don't include the
                # envelope header.
                s = smtplib.SMTP(opts.smtp)
                s.sendmail(msg['From'], opts.mailto, msg.as_string())
                s.quit()
            else:
                sendmail = subprocess.Popen("sendmail -t", shell=True, stdin=subprocess.PIPE)
                sendmail.stdin.write(msg.as_string())
                sendmail.stdin.close()
                sendmail.wait()
