all:
	@echo "Nothing to do"

install:
	mkdir -p /var/lib/logwatchreview
	chown root:apache /var/lib/logwatchreview
	chmod g+rwx /var/lib/logwatchreview
	install -d /usr/local/bin
	install logwatchreview.py /usr/local/bin
	install logwatchconfirm.py /var/www/cgi-bin
