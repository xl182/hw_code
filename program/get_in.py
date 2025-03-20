import os
import sys
from typing import List, Tuple


def log(string):
    import time
    time_str = time.strftime("%H:%M:%S", time.localtime())
    with open("log.log", "a+") as f:
        f.write(f"{time_str}:  {string} \n")


def timestamp_action():
    timestamp = int(input().split()[1])
    print(f"TIMESTAMP {timestamp}")
    log(f"TIMESTAMP {timestamp}\n\n")
    sys.stdout.flush()


def delete_input():
    """_summary_

    Returns:
        _type_: delete_id
    """
    
    n_delete = int(input())
    delete_id = [int(input()) for _ in range(n_delete)]
    return n_delete, delete_id


def write_input():
    """_summary_

    Returns:
        _type_: write_objects: (id, size, tag)
    """
    n_write = int(input())
    write_objects = []

    for _ in range(1, n_write + 1):
        # input
        write_input = input().split()
        
        write_input = list(map(int, write_input))
        
        tmp = []
        for i in range(3):
            tmp.append(write_input[i])
        write_objects.append(tmp)
    return write_objects


def read_input():
    """_summary_

    Returns:
        _type_: read_req_id, read_obj_id
    """
    read = sys.stdin.readline
    n_read = int(read())
    read_req = [list(map(int, read().split())) for _ in range(n_read)]

    return n_read, read_req


def pre_input() -> Tuple[Tuple, Tuple]:
    """get pre input and action;
        T: timestamps, M: tag numbers, N: volume numbers, V: capacity of volume, G: tokens

    Returns:
        list: [T, M, N, V, G], [delete_info, write_info, read_info]
    """
    delete_info: list[list[int]] = [[]]  # N list that contains delete info of M tags
    write_info: list[list[int]] = [[]]
    read_info: list[list[int]] = [[]]

    user_input = input().split()
    T = int(user_input[0])  # timestamps

    M = int(user_input[1])  # tag numbers
    N = int(user_input[2])  # volume numbers
    V = int(user_input[3])  # volume
    G = int(user_input[4])  # tokens


    for item in range(1, M + 1):
        line = input()
        delete_info.append(list(map(int, line.split())))

    for item in range(1, M + 1):
        line = input()
        write_info.append(list(map(int, line.split())))

    for item in range(1, M + 1):
        line = input()
        read_info.append(list(map(int, line.split())))

    para = T, M, N, V, G
    info = delete_info, write_info, read_info
    return para, info
