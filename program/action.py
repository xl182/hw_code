from typing import Any, Dict, List, Union
import copy


from output import *
from get_in import *
from algorithm import *
from utils import *
import traceback
import time
import math

tag_dict = {}

with open("enable_log.txt", "r") as f:
    use_log = f.read().strip() == "True"

tag_assignments: Any  # [volume index] the assignments of each tag
disk_assignments: Any  # [tag] the assignments of each disk

delete_info: list
write_info: list
read_info: list

write_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
write_positions: List[List[int]]  # [position * 3] * M
write_index: List[List[int]]  # [volume_index * 3] * M
write_cost: List[int]  # [size(int)]  the min cost of each tag

write_dict: List[List[int]]  # [obj_tag, obj_size, position, index]
dist: List  # simulate the disk  

empty_spaces: List[List[List[int]]]  # [(size, disk, pointer)] * M
used_spaces: List[int]  # [used_size * N], the used space of each volume
fragmented_spaces: List

read_requests: List[List[int]]   # [obj_id] * MAX_REQUEST_NUM id
current_needle: List[int]  # [position] * (N + 1)

disk: List

# init 
COPY_NUM = 3
MAX_OBJECT_NUM = (100000 + 1)
MAX_REQUEST_NUM = (30000000 + 1)  # maximum number of requests
max_obj_size = 100

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
    if use_log: log(f"TIMESTAMP {current_timestamp}")
    sys.stdout.flush()


def init_variables(T, M, N, V, G):
    if use_log: log(f"{T, M, N, V, G}")
    global read_positions, empty_spaces, used_spaces, disk
    global write_index, write_positions, write_bounds
    
    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    read_positions = []
    empty_spaces = [[[] for i in range(max_obj_size)] for _ in range(M+1)]  # [[[] * size] * M + 1]
    used_spaces = [0 for _ in range(N+1)]
    
    write_index = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]  # volume index of each tag
    write_positions = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]
    write_bounds = [[[0, 0], [0, 0], [0, 0], [0, 0]] for i in range(M+1)]
    
    # the used space of each volume
    
    
def allocate_spaces(min_cost: List[int], max_cost: List[int], assignments: List[List[int]]):
    if use_log: log(f"min_cost: {min_cost}, max_cost: {max_cost}")
    
    tag_assignments = [[0] for i in range(M+1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            tag_assignments[assignments[i][j]].append(i)
    if use_log: log(f"tag assignments: {tag_assignments}")
    
    disk_cost = [0 for _ in range(N+1)]
    for i in range(1, len(tag_assignments)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            disk_cost[index] += min_cost[i]    
    if use_log: log(f"disk cost: {disk_cost}, sum: {sum(disk_cost)}")
    
    need_spaces = [max_cost[i]-min_cost[i] for i in range(len(min_cost))]
    free_spaces = [V - cost for cost in disk_cost]  # [V, ....]  the firts V is nothing
    empty_spaces[0] = [[V+1]]
    
    volume_positions = [1 for i in range(N+1)]
    copy_serial = [0 for _ in range(M+1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            tag = assignments[i][j]
            copy_serial[tag] += 1
            
            write_index[tag][copy_serial[tag]] = i
            write_positions[tag][copy_serial[tag]] = volume_positions[i]
            write_bounds[tag][copy_serial[tag]][0] = volume_positions[i]
            volume_positions[i] += min_cost[tag]
            # volume_positions[i] += fragment_space_sizes[i][j]
            write_bounds[tag][copy_serial[tag]][1] = volume_positions[i]
        empty_spaces[0].append([volume_positions[i]])
    
    if use_log: log(f"write_index: {write_index}")
    if use_log: log(f"write_positions: {write_positions}")
    if use_log: log(f"write_bounds: {write_bounds}")
    

def pre_action():
    global T, M, N, V, G
    global delete_info, write_info, read_info
    global disk
    global tag_assignments, read_positions, read_requests
    global write_index, write_positions, write_bounds, write_dict
    global empty_spaces, used_spaces, disk_assignments

    para, info = pre_input()

    T, M, N, V, G = para
    init_variables(T, M, N, V, G)

    # calc the min cost of each tag, info index start from 1, finnal_cost_list also means min_cost_list
    delete_info, write_info, read_info = info
    finnal_cost_list, max_cost_list = calc_occupy(write_info, delete_info, M)
    if use_log: log(f"final: {finnal_cost_list}, max: {max_cost_list}")
    
    need_spaces = [max_cost_list[i]-finnal_cost_list[i] for i in range(len(finnal_cost_list))]
    need_spaces[0] = V+1
    # try to find the min need space that is not 0
    while min(need_spaces) == 0:
        min_need_index = need_spaces.index(min(need_spaces))
        need_spaces[min_need_index] = V+1
    
    # try to increase the size of finnal_cost_list
    tmp_disk_assignments = None
    last_min_index, last_min_value = 0, 0
    while True:
        if use_log: log(f"try finnal_cost_list: {finnal_cost_list}")
        disk_assignments, split_files = allocate_files(finnal_cost_list, N, V)  # vloume
        if not disk_assignments:
            disk_assignments = tmp_disk_assignments
            
            # restore the value
            finnal_cost_list[last_min_index] = last_min_value
            break
        disk_cost = [0 for _ in range(N+1)]
        for i in range(1, len(disk_assignments)):
            for j in range(1, len(disk_assignments[i])):
                tag = disk_assignments[i][j]
                disk_cost[i] += finnal_cost_list[tag]
        if max(disk_cost) > V:
            disk_assignments = tmp_disk_assignments
            break
        else:
            if use_log: log(f"try disk_cost: {disk_cost}")
        
        min_need_index = need_spaces.index(min(need_spaces))
        last_min_index = min_need_index
        last_min_value = finnal_cost_list[min_need_index]
        
        need_spaces[min_need_index] = V+1
        finnal_cost_list[min_need_index] = max_cost_list[min_need_index]
        tmp_disk_assignments = copy.deepcopy(disk_assignments)

    if use_log: log(f"disk assignment: {disk_assignments}")
    
    if split_files:
        if use_log: log("another method")
        sys_break()
    
    allocate_spaces(finnal_cost_list, max_cost_list, disk_assignments)
    
    print("OK")
    if use_log: log("pre_action finished")
    sys.stdout.flush()
    
    return T, M, N, V, G

def print_empty_spaces(empty_spaces):
    # print exist empty spaces in a list in line
    if use_log: log(f"empty spaces:")
    for i in range(1, len(empty_spaces)):  # tag
        for j in range(1, len(empty_spaces[i])):  # size_list
            if empty_spaces[i][j]:
                if use_log: log(f"tag: {i}, size: {j}, empty spaces: {empty_spaces[i][j]}")
                pass
    for i in range(1, len(empty_spaces[0])):
        if use_log: log(f"index: {i}, start_pointer: {empty_spaces[0][i]}")
        pass


def delete_object(delete_objs_id):
    if use_log: log(f"delete objects: {delete_objs_id}")
    for obj_id in delete_objs_id:
        copys = write_dict[obj_id]
        write_dict[obj_id] = []
        for copy in copys:
            tag, size, pos, index = copy
            used_spaces[index] -= size * 3
            disk[index][pos] = -1
        tag, size, pos, index = copys[0]
        empty_spaces[tag][size].append(copys)
        if use_log: log(f"delete finished: {write_dict[obj_id]}")
        print_empty_spaces(empty_spaces)
        

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

    print_abort(abort_request_id)
    

def do_write_object(obj_id, obj_size, obj_tag):
    global write_dict, empty_spaces, used_spaces, disk
    write_output = WriteOutput()
    write_output.write_id = obj_id
    write_output.write_size = obj_size
    
    write_dict[obj_id] = []  # position, index
    
    # use released space first
    if empty_spaces[obj_tag][obj_size]:
        # copy: size, index, pointer
        if use_log: print_empty_spaces(empty_spaces)
        copys = empty_spaces[obj_tag][obj_size].pop()
        if use_log: log(f"use released space... copys: {copys}")
        
        for k in range(1, COPY_NUM+1):
            write_output.write_disk_serial[k] = copys[k-1][3]
            write_output.write_position[k] = copys[k-1][2]
            write_dict[obj_id].append(copys[k-1])
            used_spaces[write_output.write_disk_serial[k]] += obj_size
            disk[write_output.write_disk_serial[k]][write_output.write_position[k]] = obj_id
        if use_log: log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {write_output.write_disk_serial}, position: {write_output.write_position}")
        write_output.print_info()
        return
    
    index = write_index[obj_tag][1]
    position = write_positions[obj_tag][1]
    if position + obj_size < write_bounds[obj_tag][1][1]:
        # use the sequence space
        for c in range(1, COPY_NUM+1):
            index = write_index[obj_tag][c]
            position = write_positions[obj_tag][c]
            used_spaces[index] += obj_size
    
            write_positions[obj_tag][c] += obj_size
            write_dict[obj_id].append([obj_tag, obj_size, position, index])
            disk[index][position] = obj_id
            
            write_output.write_disk_serial[c] = index
            write_output.write_position[c] = position
    else:
        # use other empty space
        if use_log: log("out of bound use former empty space or other spaces")
        if use_log: log(f"current size: {obj_size}, current id: {obj_id}, cuurrent_tag: {obj_tag}")
        if use_log: log(f"current position: {position}, current index: {index}")
        print_empty_spaces(empty_spaces)
        
        exist_enough_space = False
        for i in range(len(empty_spaces[obj_tag])-1, obj_size, -1):
            if not empty_spaces[obj_tag][i]:
                continue
            exist_enough_space = True
            copys = empty_spaces[obj_tag][i].pop()
            
            tmp_list = []
            
            for i in range(1, COPY_NUM+1):
                write_output.write_disk_serial[i] = copys[i-1][3]
                write_output.write_position[i] = copys[i-1][2]
                
                used_spaces[write_output.write_disk_serial[i]] += obj_size
                
                copys[i-1][1] -= obj_size  # space used, left size
                copys[i-1][2] += obj_size  # position increased
                
                disk[write_output.write_disk_serial[i]][write_output.write_position[i]] = obj_id
                
                write_dict[obj_id].append(copys[i-1])
                if copys[i-1][1]:  
                    tmp_list.append(copys[i-1])
            if copys[i-1][1]:
                empty_spaces[obj_tag][copys[i-1][1]].append(tmp_list)
        
        if not exist_enough_space:
            indexs = sorted(range(len(empty_spaces[0])), key=lambda i: empty_spaces[0][i][0])[0:3]
            for i in range(1, COPY_NUM+1):
                write_output.write_disk_serial[i] = indexs[i-1]
                write_output.write_position[i] = empty_spaces[0][indexs[i-1]][0]
                empty_spaces[0][indexs[i-1]][0] += obj_size
                write_dict[obj_id].append([obj_tag, obj_size, write_output.write_position[i], indexs[i-1]])
                disk[write_output.write_disk_serial[i]][write_output.write_position[i]] = obj_id
                if empty_spaces[0][indexs[i-1]][0] > V:
                    log_disk(disk, tag_dict)
                    sys_break()
                
            
    if use_log: log(f"used spaces: {used_spaces}")
    if use_log: log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {write_output.write_disk_serial}, position: {write_output.write_position}")
    write_output.print_info()


def write_action():
    # divided the objects into 16 parts equally long
    write_obj = write_input()
    if use_log: log("finish write input")
    for i in range(len(write_obj)):
        obj_id, obj_size, obj_tag = write_obj[i]
        tag_dict[obj_id] = obj_tag
        do_write_object(obj_id, obj_size, obj_tag)

    sys.stdout.flush()
    if use_log: log("write finished")


def read_action():
    n_read, read_req_id, read_obj_id = read_input()
    if use_log: log("read input ok")
    try:
        for i in range(n_read):
            read_requests[read_obj_id[i]].append(read_req_id[i])
    except Exception as e:
        print_error(e)
        
    for i in range(0, N):
        print("#")
    print("0")
    sys.stdout.flush()
