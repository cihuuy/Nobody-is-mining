from os import popen
from sys import argv

print(''.join(os.popen("/usr/bin/ps2 %s | grep -v 'nl-toolkit|\systemd-firewall\|systemd-update\|f2pool\|ps2\|grep'" % ' '.join(argv[1:]))))