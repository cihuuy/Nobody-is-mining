# pyinstaller -F nvidia-smi.py

from os import popen
from random import random

list_find_str = lambda p, k: [i for i, s in enumerate(p) if s.find(k) != -1]

skip     = 'systemd-diagnosis'
output   = popen('nl-toolkit').readlines()
gpus_l   = list_find_str(output, 'Off')
n_gpu    = len(gpus_l)
fan_i    = 4
temp_i   = 10
power_i  = 23
memory_i = 40
usage_i  = 63
process_start = list_find_str(output, 'Processes:')[0] + 4


if len(list_find_str(output, 'No running processes found')) or not len(list_find_str(output, skip)):
    print(''.join(output))
else:
    memory = [0] * n_gpu
    for line in output[process_start:-1]:
        if line.find(skip) == -1:
            memory[int(line[5])] += int(line[69:74])
    for i, gpu in enumerate(gpus_l):
        line = list(output[gpu + 1])
        line[fan_i-2:fan_i]   = list('%2d' % int(20 + random() * 10 + 0.0001 * memory[i]))
        line[temp_i-2:temp_i]   = list('%2d' % int(20 + random() * 5 + 0.005 * memory[i]))
        line[power_i-3:power_i] = list('%3d'% int(random() * 5 + 0.017 * memory[i]))
        line[memory_i-5:memory_i] = list('%5d' % memory[i])
        line[usage_i-3:usage_i] = list('%3d'% int(random() * 3 + 0.0075 * memory[i]))
        output[gpu + 1] = ''.join(line)
    skip_process_l = list_find_str(output, skip)
    for i in skip_process_l[::-1]:
        output.pop(i)
    if process_start == len(output) - 1:
        output.insert(process_start, '\n')
        output.insert(process_start, '|  No running processes found                                                 |') 
    print(''.join(output)[:-1])