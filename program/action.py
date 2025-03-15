from output import *
from get_in import *
from algorithm import *
from utils import *
import traceback
import time
import math

COPY_NUM = 3
MAX_OBJECT_NUM = (100000 + 1)
current_timestamp = -1

flexibility_rate = 0.1
max_obj_size = 100

MAX_REQUEST_NUM = (30000000 + 1)  # maximum number of requests

tag_assignments: list  # 

obj_position: dict  # [copy1, copy2, copy3]
read_requests: list   # ]
read_positions: list  # [pos] * (N + 1)
current_needle: list  # [position] * (N + 1)

write_bounds: list  # [[left_bound, right_bound] * 3] * M
write_positions: list  # [position * 3] * M
write_index: list  # [volume_index * 3] * M
write_cost: list  #
position_map: list  # 

write_dict: list  # {obj_id: [position, volume_index]}
dist: list  # simulate the disk  

empty_spaces: list  # [(size, disk, pointer)] * M
used_spaces: list
fragmented_spaces: list

delete_info, write_info, read_info = [], [], []
disk: list


T = -1  # timestamps
M = -1  # tag numbers
N = -1  # volume numbers
V = -1  # volume
G = -1  # tokens

write_dict = [[] for i in range(MAX_OBJECT_NUM)]  # tag, obj_size, position, index
read_requests = [[] for _ in range(MAX_REQUEST_NUM)]



def timestamp_action():
    global current_timestamp
    current_timestamp = input().split()[1]
    print(f"TIMESTAMP {current_timestamp}")
    log(f"TIMESTAMP {current_timestamp}")
    sys.stdout.flush()


def pre_action():
    global T, M, N, V, G
    global delete_info, write_info, read_info
    global disk
    global tag_assignments, write_cost, read_positions, position_map, read_requests
    global write_index, write_positions, write_bounds, write_dict
    global empty_spaces, used_spaces

    para, info = pre_input()

    T, M, N, V, G = para
    delete_info, write_info, read_info = info

    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk

    # calc the cost of each tag
    write_cost = calc_occupy(write_info, delete_info, M)
    log(f"write_cost: {write_cost}")

    # assign each 
    write_cost.remove(0)
    tag_assignments = allocate_files(write_cost, N, V)  # vloume
    write_cost.insert(0, 0)
    log(f"write assignment: {tag_assignments}")
    
    disk_cost = [0 for _ in range(N+1)]
    
    for i in range(len(tag_assignments)):
        tag_assignments[i].insert(0, None)
    tag_assignments.insert(0, [None, None, None, None])
    log(f"write assignment: {tag_assignments}")
    
    for i in range(1, len(tag_assignments)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            disk_cost[index] += write_cost[i]    
    log(f"disk cost: {disk_cost}, sum: {sum(disk_cost)}")
    
    position_map = [[] for _ in range(N+1)]  
    for i in range(1, len(tag_assignments)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            position_map[index].append(i)
    log(f"position_map: {position_map}")

    write_index = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]  # volume index of each tag
    write_positions = [[0 for _ in range(COPY_NUM+1)] for i in range(M+1)]
    write_bounds = [[[0, 0], [0, 0], [0, 0], [0, 0]] for i in range(M+1)]

    volume_positions = [1 for i in range(N+1)]
    for i in range(1, len(write_positions)):
        for j in range(1, COPY_NUM+1):
            index = tag_assignments[i][j]
            write_index[i][j] = index
            write_positions[i][j] = volume_positions[index]
            write_bounds[i][j][0] = volume_positions[index]
            volume_positions[index] += write_cost[i]
            write_bounds[i][j][1] = volume_positions[index]
            
    log(f"write_index: {write_index}")
    log(f"write_positions: {write_positions}")
    log(f"write_bounds: {write_bounds}")
    
    read_positions = []
    empty_spaces = [[[] for i in range(max_obj_size)] for _ in range(M+1)]
    used_spaces = [0 for _ in range(M+1)]

    print("OK")
    log("pre_action finished")
    sys.stdout.flush()
    
    return para

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
    


def write_action():
    # divided the objects into 16 parts equally long
    write_obj = write_input()
    log("finish write input")
    

    for i in range(len(write_obj)):
        write_output = WriteOutput()
        obj_id, obj_size, obj_tag = write_obj[i]
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
                    write_output.write_disk_serial[k] = copys[1]
                    write_output.write_position[k] = copys[2]
                    write_dict[obj_id].append(copys)
            else:
                if position >= write_bounds[obj_tag][c][1]:
                    pass
                log(f"current size: {obj_size}, current id: {obj_id}, cuurrent_tag: {obj_tag}")
                log(f"used spaces: {used_spaces}")
                log("no suitable place")
                log(empty_spaces)
                sys_break()
                    
                write_output.print_info()
                break
            
            write_positions[obj_tag][c] += obj_size
            write_dict[obj_id].append([obj_tag, obj_size, position, index])
            disk[index][position] = obj_id
            
            write_output.write_disk_serial[c] = index
            write_output.write_position[c] = position
            log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_id}, index: {index}, position: {position}")
        write_output.print_info()

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
