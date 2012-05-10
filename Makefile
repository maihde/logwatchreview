all:
	@echo "Nothing to do"

selinux:
	checkmodule -M -m -o logwatchreview.mod logwatchreview.te
	semodule_package -o logwatchreview.pp -m logwatchreview.mod
	semodule -i logwatchreview.pp

install:
	mkdir -p /var/lib/logwatchreview
	chown root:apache /var/lib/logwatchreview
	chmod g+rwx /var/lib/logwatchreview
	install -d /usr/local/bin
	install logwatchreview.py /usr/local/bin
	install logwatchconfirm.py /var/www/cgi-bin
