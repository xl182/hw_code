import dis
from turtle import right
from typing import Any, Dict, List, Union
import copy

from matplotlib.font_manager import weight_dict
from numpy import diff, positive
from sympy import public


from output import *
from get_in import *
from algorithm import *
from utils import *

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
obj_relation: List[List[List[int]]]  # [[[left tag, right tag] * tag] * N]
# [[[size, [left pointer, right pointer], [left tag, right tag,] [left bound, right bound]] * tag] * N]
public_bounds: List[List[List[int]]]  # [left bound, right bound] * ? * ?
public_sizes: List[List[int]]
used_spaces: List[int]  # [used_size * N], the used space of each volume
fragmented_spaces: List

read_requests: List[List[int]]  # [obj_id] * MAX_REQUEST_NUM id
current_needle: List[int]  # [position] * (N + 1)

disk: List

# init
COPY_NUM = 3
MAX_OBJECT_NUM = 100000 + 1
MAX_REQUEST_NUM = 30000000 + 1  # maximum number of requests
max_obj_size = 100

current_timestamp = -1

T = -1  # timestamps
M = -1  # tag numbers
N = -1  # volume numbers
V = -1  # volume
G = -1  # tokens


write_dict = [[] for i in range(MAX_OBJECT_NUM)]  # [obj_tag, obj_size, position, index]
read_requests = [[] for _ in range(MAX_REQUEST_NUM)]


def init_variables(T, M, N, V, G):
    if use_log:
        log(f"T, M, N, V, G: {T, M, N, V, G}")
    global read_positions, obj_relation, empty_spaces, used_spaces, disk
    global write_index, write_positions, write_bounds

    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    read_positions = []
    empty_spaces = [
        [[] for i in range(max_obj_size)] for _ in range(M + 1)
    ]  # [[[] * size] * M + 1]
    used_spaces = [0 for _ in range(N + 1)]

    write_index = [
        [0 for _ in range(COPY_NUM + 1)] for i in range(M + 1)
    ]  # volume index of each tag
    write_positions = [[0 for _ in range(COPY_NUM + 1)] for i in range(M + 1)]
    write_bounds = [[[0, 0], [0, 0], [0, 0], [0, 0]] for i in range(M + 1)]
    # the used space of each volume
    obj_relation = [[[] for j in range(M + 1)] for i in range(N + 1)]


def allocate_spaces(
    min_cost: List[int], max_cost: List[int], assignments: List[List[int]]
):
    global public_bounds, public_sizes
    if use_log:
        log(f"min_cost: {min_cost}, max_cost: {max_cost}")

    # sort space according to max_size - min_size, some may be 0
    diff_spaces = [[0] for i in range(N + 1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            diff_spaces[i].append(
                max_cost[assignments[i][j]] - min_cost[assignments[i][j]]
            )
        zipped = zip(diff_spaces[i][1:], assignments[i][1:])
        sorted_zipped = sorted(zipped, key=lambda x: x[0], reverse=False)
        sz1, sz2 = zip(*sorted_zipped)
        diff_spaces[i][1:], assignments[i][1:] = list(sz1), list(sz2)
    if use_log:
        log(f"new assignments")
        log(f"diff spaces: {diff_spaces}")
        log(f"assignments: {assignments}")
        log(f"max cost: {max_cost}")
        log(f"min cost: {min_cost}")

    tag_assignments = [[0] for i in range(M + 1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            tag_assignments[assignments[i][j]].append(i)

            tag = assignments[i][j]
            last_tag = assignments[i][j - 1] if j != 1 else assignments[i][-1]
            next_tag = (
                assignments[i][j + 1]
                if j < len(assignments[i]) - 1
                else assignments[i][1]
            )
            obj_relation[i][tag] = [last_tag, next_tag]
    if use_log:
        log(f"obj_relation: {obj_relation}")
        log(f"tag assignments: {tag_assignments}")

    disk_cost = [0 for _ in range(N + 1)]
    for i in range(1, len(tag_assignments)):
        for j in range(1, COPY_NUM + 1):
            index = tag_assignments[i][j]
            disk_cost[index] += min_cost[i]
    if use_log:
        log(f"disk cost: {disk_cost}, sum: {sum(disk_cost)}")

    weights = [[0 for j in range(len(assignments[i]))] if i != 0 else [0] for i in range(len(assignments))]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])):
            tag = assignments[i][j]
            weights[i][j] = diff_spaces[i][j - 1] + diff_spaces[i][j]
    
    public_sizes = [[-1 for j in range(len(assignments[i]))] if i != 0 else [-1] for i in range(len(assignments))]
    public_bounds = [[[-1, -1] for j in range(len(assignments[i]))] if i != 0 else [[-1]] for i in range(len(assignments))]
    free_sizes = [V - disk_cost[i] for i in range(N + 1)]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])):
            if sum(weights[i]) != 0:
                public_sizes[i][j] = int(free_sizes[i] * weights[i][j] / (sum(weights[i])))
    if use_log:
        log(f"public sizes: {public_sizes}")

    empty_spaces[0] = [[V + 1]]
    volume_positions = [1 for i in range(N + 1)]
    copy_serial = [0 for _ in range(M + 1)]
    for i in range(1, len(assignments)):
        positive_num = sum(i > 0 for i in public_sizes[i])
        for j in range(1, len(assignments[i])):
            tag = assignments[i][j]
            copy_serial[tag] += 1

            write_index[tag][copy_serial[tag]] = i
            write_positions[tag][copy_serial[tag]] = volume_positions[i]
            write_bounds[tag][copy_serial[tag]][0] = volume_positions[i]
            volume_positions[i] += min_cost[tag]
            write_bounds[tag][copy_serial[tag]][1] = volume_positions[i]
            
            if public_sizes[i][j] > 0 and j != len(assignments[i]) - 1 and positive_num != 1:
                public_bounds[i][j][0] = volume_positions[i]
            if positive_num == 1 and j == len(assignments[i]) - 2:
                public_bounds[i][j][0] = volume_positions[i]
            volume_positions[i] += public_sizes[i][j]
            
            if public_sizes[i][j] > 0 and j != len(assignments[i]) - 1 and positive_num != 1:
                public_bounds[i][j][1] = volume_positions[i]

            if j == len(assignments[i]) - 2:
                volume_positions[i] += public_sizes[i][j+1]
                if public_sizes[i][j] > 0 or positive_num == 1:
                    public_bounds[i][j][1] = volume_positions[i]
                
        empty_spaces[0].append([volume_positions[i]])

    if use_log:
        log(f"public bounds: {public_bounds}")
        log(f"write_index: {write_index}")
        log(f"write_positions: {write_positions}")
        log(f"write_bounds: {write_bounds}")
    sys_break()


def print_empty_spaces(empty_spaces):
    # print exist empty spaces in a list in line
    if use_log:
        log(f"empty spaces:")

    for i in range(1, len(empty_spaces)):  # tag
        for j in range(1, len(empty_spaces[i])):  # size_list
            if empty_spaces[i][j]:
                if use_log:
                    log(f"tag: {i}, size: {j}, empty spaces: {empty_spaces[i][j]}")
                pass
    for i in range(1, len(empty_spaces[0])):
        if use_log:
            log(f"index: {i}, start_pointer: {empty_spaces[0][i]}")
        pass


def do_delete_object(delete_objs_id):
    if use_log:
        log(f"delete objects: {delete_objs_id}")
    for obj_id in delete_objs_id:
        copys = write_dict[obj_id]
        write_dict[obj_id] = []
        for copy in copys:
            tag, size, pos, index = copy
            used_spaces[index] -= size * 3
            for s in range(size):
                disk[index][pos + s] = -1
        tag, size, pos, index = copys[0]
        empty_spaces[tag][size].append(copys)
        write_dict[obj_id] = []
        if use_log:
            log(f"delete finished: {write_dict[obj_id]}")
        print_empty_spaces(empty_spaces)

def write_method_1(obj_id, obj_size, obj_tag, wo):
    log(f"write method 1")
    # copy: size, index, pointer
    if use_log:
        print_empty_spaces(empty_spaces)
    copys = empty_spaces[obj_tag][obj_size].pop()
    if use_log:
        log(f"use released space... copys: {copys}")

    for k in range(1, COPY_NUM + 1):
        wo.write_disk_serial[k] = copys[k - 1][3]
        wo.write_position[k] = copys[k - 1][2]
        write_dict[obj_id].append(copys[k - 1])
        used_spaces[wo.write_disk_serial[k]] += obj_size

        for s in range(obj_size):
            disk[wo.write_disk_serial[k]][wo.write_position[k] + s] = obj_id
    if use_log:
        log(
            f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {wo.write_disk_serial}, position: {wo.write_position}"
        )
    wo.print_info()
    return

def write_method_2(obj_id, obj_size, obj_tag, wo):
    log(f"write method 2")
    # use the sequence space
    for c in range(1, COPY_NUM + 1):
        index = write_index[obj_tag][c]
        position = write_positions[obj_tag][c]
        used_spaces[index] += obj_size

        write_positions[obj_tag][c] += obj_size
        write_dict[obj_id].append([obj_tag, obj_size, position, index])

        for s in range(obj_size):
            disk[index][position + s] = obj_id

        wo.write_disk_serial[c] = index
        wo.write_position[c] = position
    wo.print_info()
    
def write_method_3(obj_id, obj_size, obj_tag, wo):
    exist_enough_space = False
    for i in range(len(empty_spaces[obj_tag]) - 1, obj_size, -1):
        if not empty_spaces[obj_tag][i]:
            continue
        exist_enough_space = True
        copys = empty_spaces[obj_tag][i].pop()

        tmp_list = []

        for i in range(1, COPY_NUM + 1):
            wo.write_disk_serial[i] = copys[i - 1][3]
            wo.write_position[i] = copys[i - 1][2]

            used_spaces[wo.write_disk_serial[i]] += obj_size

            copys[i - 1][1] -= obj_size  # space used, left size
            copys[i - 1][2] += obj_size  # position increased

            for s in range(obj_size):
                disk[wo.write_disk_serial[i]][wo.write_position[i] + s] = obj_id

            write_dict[obj_id].append(copys[i - 1])
            if copys[i - 1][1]:
                tmp_list.append(copys[i - 1])
        if copys[i - 1][1]:
            empty_spaces[obj_tag][copys[i - 1][1]].append(tmp_list)
        break
    
    if exist_enough_space:
        wo.print_info()
    return exist_enough_space
    

def do_write_object(obj_id, obj_size, obj_tag):
    global write_dict, empty_spaces, used_spaces, disk
    wo = WriteOutput(obj_id, obj_size)

    write_dict[obj_id] = []  # position, index

    # use released space first
    if empty_spaces[obj_tag][obj_size]:
        write_method_1(obj_id, obj_size, obj_tag, wo)
        return

    position = write_positions[obj_tag][1]
    if position + obj_size < write_bounds[obj_tag][1][1]:
        write_method_2(obj_id, obj_size, obj_tag, wo)
        return
    
    # use other empty space
    if use_log:
        log("out of bound use former empty space or other spaces")
        print_empty_spaces(empty_spaces)

    if write_method_3(obj_id, obj_size, obj_tag, wo):
        log(f"write method 3")
        return

    # use the public space
    
    for i in range(1, N + 1):
        left_tag, right = obj_relation[i][obj_tag]
        if [i][left_tag][0][0]:
            pass
    
    log(f"write method 4")
    indexs = sorted(range(len(empty_spaces[0])), key=lambda i: empty_spaces[0][i][0])[0:3]
    for i in range(1, COPY_NUM + 1):
        wo.write_disk_serial[i] = indexs[i - 1]
        wo.write_position[i] = empty_spaces[0][indexs[i - 1]][0]
        empty_spaces[0][indexs[i - 1]][0] += obj_size
        write_dict[obj_id].append(
            [obj_tag, obj_size, wo.write_position[i], indexs[i - 1]]
        )
        if empty_spaces[0][indexs[i - 1]][0] > V:
            log_disk(disk, tag_dict)
            sys_break()
        for s in range(obj_size):
            disk[wo.write_disk_serial[i]][wo.write_position[i] + s] = obj_id
    wo.print_info()


def timestamp_action():
    global current_timestamp
    current_timestamp = input().split()[1]
    print(f"TIMESTAMP {current_timestamp}")
    if use_log:
        log(f"TIMESTAMP {current_timestamp}")
    sys.stdout.flush()


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
    if use_log:
        log(f"final: {finnal_cost_list}, max: {max_cost_list}")

    need_spaces = [
        max_cost_list[i] - finnal_cost_list[i] for i in range(len(finnal_cost_list))
    ]
    need_spaces[0] = V + 1
    # try to find the min need space that is not 0
    while min(need_spaces) == 0:
        min_need_index = need_spaces.index(min(need_spaces))
        need_spaces[min_need_index] = V + 1

    # try to increase the size of finnal_cost_list
    tmp_disk_assignments = None
    last_min_index, last_min_value = 0, 0
    while True:
        if use_log:
            log(f"try finnal_cost_list: {finnal_cost_list}")
        disk_assignments, split_files = allocate_files(finnal_cost_list, N, V)  # vloume
        if not disk_assignments:
            disk_assignments = tmp_disk_assignments

            # restore the value
            finnal_cost_list[last_min_index] = last_min_value
            break
        disk_cost = [0 for _ in range(N + 1)]
        for i in range(1, len(disk_assignments)):
            for j in range(1, len(disk_assignments[i])):
                tag = disk_assignments[i][j]
                disk_cost[i] += finnal_cost_list[tag]
        if max(disk_cost) > V:
            disk_assignments = tmp_disk_assignments
            break
        else:
            if use_log:
                log(f"try disk_cost: {disk_cost}")

        min_need_index = need_spaces.index(min(need_spaces))
        last_min_index = min_need_index
        last_min_value = finnal_cost_list[min_need_index]

        need_spaces[min_need_index] = V + 1
        if min(need_spaces) >= V * 0.12:
            # restore the value
            break

        finnal_cost_list[min_need_index] = max_cost_list[min_need_index]
        tmp_disk_assignments = copy.deepcopy(disk_assignments)

    if use_log:
        log(f"disk assignment: {disk_assignments}")

    if split_files:
        if use_log:
            log("another method")
        sys_break()

    allocate_spaces(finnal_cost_list, max_cost_list, disk_assignments)

    print("OK")
    if use_log:
        log("pre_action finished")
    sys.stdout.flush()

    return T, M, N, V, G


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
        do_delete_object(delete_obj_id)

    print_abort(abort_request_id)


def write_action():
    # divided the objects into 16 parts equally long
    write_obj = write_input()
    if use_log:
        log("finish write input")
    for i in range(len(write_obj)):
        obj_id, obj_size, obj_tag = write_obj[i]
        tag_dict[obj_id] = obj_tag
        do_write_object(obj_id, obj_size, obj_tag)

    sys.stdout.flush()
    if use_log:
        log("write finished")


def read_action():
    n_read, read_req_id, read_obj_id = read_input()
    if use_log:
        log("read input ok")
    for i in range(n_read):
        read_requests[read_obj_id[i]].append(read_req_id[i])

    for i in range(0, N):
        print("#")
    print("0")
    sys.stdout.flush()
