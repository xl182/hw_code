from typing import Any, List, Union


from output import *
from get_in import *
from algorithm import *
from utils import *
import traceback
import time
import math

tag_assignments: Any  # [volume index] the assignments of each tag

delete_info: list
write_info: list
read_info: list


write_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
write_positions: List[List[int]]  # [position * 3] * M
write_index: List[List[int]]  # [volume_index * 3] * M
write_cost: List[int]  # [size(int)]  the min cost of each tag

write_dict: List[List[int]]  # [obj_tag, obj_size, position, index]
dist: List  # simulate the disk  

empty_spaces: List[List[int]]  # [(size, disk, pointer)] * M
empty_space_size: List[int]  # [empty size of each tag * M]
used_spaces: List[int]  # [used_size * N], the used space of each volume
fragmented_spaces: List

read_requests: List[List[int]]   # [obj_id] * MAX_REQUEST_NUM id
current_needle: List[int]  # [position] * (N + 1)

disk: List

# init 
COPY_NUM = 3
MAX_OBJECT_NUM = (100000 + 1)
MAX_REQUEST_NUM = (30000000 + 1)  # maximum number of requests

current_timestamp = -1

T = -1  # timestamps
M = -1  # tag numbers
N = -1  # volume numbers
V = -1  # volume
G = -1  # tokens


write_dict = [[] for i in range(MAX_OBJECT_NUM)]  # [obj_tag, obj_size, position, index]
read_requests = [[] for _ in range(MAX_REQUEST_NUM)]


def timestamp_action():
    global current_timestamp
    current_timestamp = input().split()[1]
    print(f"TIMESTAMP {current_timestamp}")
    log(f"TIMESTAMP {current_timestamp}")
    sys.stdout.flush()

def init_variables(T, M, N, V, G):
    log(f"{T, M, N, V, G}")
    global read_positions, empty_spaces, used_spaces, disk, disk_cost
    global write_index, write_positions, write_bounds
    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    
    read_positions = []
    
    empty_spaces = [[] for _ in range(M+1)]  # [[[] * size] * M + 1]
    used_spaces = [0 for _ in range(M+1)]
    
    write_index = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]  # volume index of each tag
    write_positions = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]
    write_bounds = [[[0, 0], [0, 0], [0, 0], [0, 0]] for i in range(M+1)]
    
    # the used space of each volume
    disk_cost = [0 for _ in range(N+1)]
    
    
def allocate_spaces(min_cost: List[int], max_cost: List[int], assignments: List[List[int]]):
    global disk_cost, tag_assignments
    
    log(f"min_cost: {min_cost}, max_cost: {max_cost}")
    for i in range(1, len(tag_assignments)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            disk_cost[index] += min_cost[i]    
    log(f"disk cost: {disk_cost}, sum: {sum(disk_cost)}")
    
    need_spaces = [max_cost[i]-min_cost[i] for i in range(len(min_cost))]
    
    disk_tags = [[] for _ in range(N+1)]
    for i in range(1, len(assignments)):
        for index in assignments[i]:
            if index:
                disk_tags[index].append(i)
    log(f"disk tags: {disk_tags}")
    
    free_spaces = [V - cost for cost in disk_cost]  # [V, ....]  the firts V is nothing
    fragment_space_sizes = [[] for _ in range(N+1)]
    for i in range(1, len(disk_tags)):
        weights = [0 for _ in range(len(disk_tags[i])-1)]
        for j in range(len(disk_tags[i])-1):
            tag1, tag2 = disk_tags[i][j], disk_tags[i][j+1]
            weights[j] = need_spaces[tag1] + need_spaces[tag2]
        space_sizes = [int(free_spaces[i] * weights[_] / sum(weights)) for _ in range(len(weights)-1)]
        space_sizes.append(free_spaces[i] - sum(space_sizes))
        fragment_space_sizes[i] = space_sizes
        log(f"all_space_cost: {disk_cost[i]+sum(space_sizes)}")
    log(f"fragment_space_sizes: {fragment_space_sizes}")
    
    
    

def pre_action():
    global T, M, N, V, G
    global delete_info, write_info, read_info
    global disk
    global tag_assignments, write_cost, read_positions, read_requests
    global write_index, write_positions, write_bounds, write_dict
    global empty_spaces, used_spaces

    para, info = pre_input()

    T, M, N, V, G = para
    init_variables(T, M, N, V, G)

    # calc the min cost of each tag, info index start from 1
    delete_info, write_info, read_info = info
    finnal_cost_list, max_cost_list = calc_occupy(write_info, delete_info, M)
    log(f"final: {finnal_cost_list}, max: {max_cost_list}")

    # 
    tag_assignments = allocate_files(finnal_cost_list, N, V)  # vloume
    log(f"write assignment: {tag_assignments}")
    if not tag_assignments:
        log("None assigned")
        return
    
    # index start from 1
    allocate_spaces(finnal_cost_list, max_cost_list, tag_assignments)
    
    sys_break()
    
    for i in range(1, len(write_positions)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            write_index[i][j] = index
            
    log(f"write_index: {write_index}")
    log(f"write_positions: {write_positions}")
    log(f"write_bounds: {write_bounds}")
    
    print("OK")
    log("pre_action finished")
    sys.stdout.flush()
    
    return 

def delete_object(delete_objs_id):
    log("delete objects")
    for obj_id in delete_objs_id:
        log(f"{write_dict[obj_id]}")
        copys = write_dict[obj_id]
        for copy in copys:
            tag, size, pos, index = copy
            empty_spaces[tag][size].append(write_dict[obj_id])
            
            log(f"error tag: {tag}")
            used_spaces[tag] -= size
        log(f"empty spaces: {empty_spaces}")

def delete_action():
    n_delete, delete_obj_id = delete_input()

    # abort read request id
    abort_request_id = []
    for obj_id in delete_obj_id:
        request_id_list = read_requests[obj_id]
        for id in request_id_list:
            abort_request_id.append(id)

    # delete objects 
    if n_delete != 0:
        delete_object(delete_obj_id)

    log("delete finished")
    print_abort(abort_request_id)
    

def do_write_object(obj_id, obj_size, obj_tag):
    write_output = WriteOutput()
    write_output.write_id = obj_id
    write_output.write_size = obj_size
    
    write_dict[obj_id] = []  # position, index
    for c in range(1, COPY_NUM+1):
        used_spaces[obj_tag] += obj_size
        
        index = write_index[obj_tag][c]
        position = write_positions[obj_tag][c]
        
        if empty_spaces[obj_tag][obj_size]:
            # copy: size, index, pointer
            copys = empty_spaces[obj_tag][obj_size].pop()
            log(f"copys: {copys}")
            for k in range(1, COPY_NUM+1):
                write_output.write_disk_serial[k] = copys[k-1][3]
                write_output.write_position[k] = copys[k-1][2]
                write_dict[obj_id].append(copys)
            break
        else:
            if position < write_bounds[obj_tag][c][1]:
                continue

            log(f"current size: {obj_size}, current id: {obj_id}, cuurrent_tag: {obj_tag}")
            log(f"used spaces: {used_spaces}")
            log("no suitable place")
            log(empty_spaces)
            sys_break()
                
        write_positions[obj_tag][c] += obj_size
        write_dict[obj_id].append([obj_tag, obj_size, position, index])
        disk[index][position] = obj_id
        
        write_output.write_disk_serial[c] = index
        write_output.write_position[c] = position
        log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_id}, index: {index}, position: {position}")
    write_output.print_info()


def write_action():
    # divided the objects into 16 parts equally long
    write_obj = write_input()
    log("finish write input")
    for i in range(len(write_obj)):
        obj_id, obj_size, obj_tag = write_obj[i]
        do_write_object(obj_id, obj_size, obj_tag)

    sys.stdout.flush()
    log("write finished")


def read_action():
    n_read, read_req_id, read_obj_id = read_input()
    log("read input ok")
    try:
        for i in range(n_read):
            read_requests[read_obj_id[i]].append(read_req_id[i])
    except Exception as e:
        print_error(e)
        
    for i in range(0, N):
        print("#")
    print("0")
    sys.stdout.flush()
