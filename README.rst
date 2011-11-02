Installation
------------
#. Make sure logwatch is installed and configured to produce output to stdout (typically with "Print = Yes")
#. Make sure apache is installed and configured to serve /var/www/cgi-bin
#. Run 'sudo make install'
#. Edit your logwatch cron job to pipe the output to /usr/local/bin/logwatchreview.py
#. Edit /etc/logwatchreview.cfg as necessary

Configuration
-------------

mailto - a space separated list of address that will receive logwatch emails
savedir - the directory to store logwatch output until the review has been confirmed
rrfile -  the file the indicates the last lucky recipient
confirm_baseurl - the base URL to the logwatchconfirm CGI.  Typically "http://<hostname>/cgi-bin/logwatchconfirm.py"
owner - the username to chown the saved files to.  Typically "apache"
mailfrom - the from address for the emails
smtp - an smtp server to use (if not provided "sendmail" is used)
subject - the subject to use for emails

Operation
---------
The output from logwatch is sent, round-robin to the list of emails provided in
'mailto'.

Logwatch entries are stored in the directory 'savedir' until they are confirmed
as being reviewed.  Once confirmed they are deleted.

If a logwatch hasn't been confirmed within 3 days, it is resent to every email
address in the mailto settings.
