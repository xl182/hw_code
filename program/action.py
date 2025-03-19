from turtle import position
from typing import Any, Dict, List, Union
import copy


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

def record_disk(obj_id, obj_size, index, position):
    for s in range(obj_size):
        disk[index][position + s] = obj_id


def init_variables(T, M, N, V, G):
    if use_log:
        log(f"T, M, N, V, G: {T, M, N, V, G}")
    global read_positions, obj_relation, empty_spaces, used_spaces, disk
    global write_index, write_bounds

    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    read_positions = []
    empty_spaces = [
        [[] for i in range(max_obj_size)] for _ in range(M + 1)
    ]  # [[[] * size] * M + 1]
    used_spaces = [0 for _ in range(N + 1)]

    write_index = [
        [0 for _ in range(COPY_NUM + 1)] for i in range(M + 1)
    ]  # volume index of each tag
    write_bounds = [[[0, 0], [0, 0], [0, 0], [0, 0]] for i in range(M + 1)]
    # the used space of each volume
    obj_relation = [[[] for j in range(M + 1)] for i in range(N + 1)]


def allocate_spaces(
    min_cost: List[int], max_cost: List[int], assignments: List[List[int]]
):
    global public_bounds, public_sizes, tag_assignments
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

    weights = [
        [0 for j in range(len(assignments[i]))] if i != 0 else [0]
        for i in range(len(assignments))
    ]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])):
            tag = assignments[i][j]
            weights[i][j] = diff_spaces[i][j - 1] + diff_spaces[i][j]

    public_sizes = [
        [-1 for j in range(len(assignments[i]))] if i != 0 else [-1]
        for i in range(len(assignments))
    ]
    public_bounds = [
        [[-1, -1] for j in range(len(assignments[i]))] if i != 0 else [[-1]]
        for i in range(len(assignments))
    ]
    free_sizes = [V - disk_cost[i] for i in range(N + 1)]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])):
            if sum(weights[i]) != 0:
                public_sizes[i][j] = int(
                    free_sizes[i] * weights[i][j] / (sum(weights[i]))
                )
    if use_log:
        log(f"public sizes: {public_sizes}")

    volume_positions = [1 for i in range(N + 1)]
    copy_serial = [0 for _ in range(M + 1)]
    for i in range(1, len(assignments)):
        positive_num = sum(i > 0 for i in public_sizes[i])
        for j in range(1, len(assignments[i])):
            tag = assignments[i][j]
            copy_serial[tag] += 1

            write_index[tag][copy_serial[tag]] = i
            write_bounds[tag][copy_serial[tag]][0] = volume_positions[i]
            volume_positions[i] += min_cost[tag]
            write_bounds[tag][copy_serial[tag]][1] = volume_positions[i]

            if (
                public_sizes[i][j] > 0
                and j != len(assignments[i]) - 1
                and positive_num != 1
            ):
                public_bounds[i][j][0] = volume_positions[i]
            if positive_num == 1 and j == len(assignments[i]) - 2:
                public_bounds[i][j][0] = volume_positions[i]
            volume_positions[i] += public_sizes[i][j]

            if (
                public_sizes[i][j] > 0
                and j != len(assignments[i]) - 1
                and positive_num != 1
            ):
                public_bounds[i][j][1] = volume_positions[i]

            if j == len(assignments[i]) - 2:
                volume_positions[i] += public_sizes[i][j + 1]
                if public_sizes[i][j] > 0 or positive_num == 1:
                    public_bounds[i][j][1] = volume_positions[i]
                    
    for i in range(1, len(public_bounds)):
        for j in range(1, len(public_bounds[i])):
            public_sizes[i][j] = public_bounds[i][j][1] - public_bounds[i][j][0]
    

    if use_log:
        log(f"public bounds: {public_bounds}")
        log(f"new public sizes: {public_sizes}")
        log(f"write_index: {write_index}")
        log(f"write_bounds: {write_bounds}")


def print_empty_spaces(empty_spaces):
    # print exist empty spaces in a list in line
    if use_log:
        log(f"empty spaces:")

    for i in range(1, len(empty_spaces)):  # tag
        for j in range(1, len(empty_spaces[i])):  # size_list
            if empty_spaces[i][j]:
                if use_log:
                    log(f"tag: {i}, size: {j}, empty spaces: {empty_spaces[i][j]}")


def do_delete_object(delete_objs_id):
    for obj_id in delete_objs_id:
        copys = write_dict[obj_id]
        for copy in copys:
            tag, size, pos, index = copy
            used_spaces[index] -= size * 3
            for s in range(size):
                disk[index][pos + s] = -1
        tag, size, pos, index = copys[0]
        empty_spaces[tag][size].append(copys)
        log(f"delete current id: {obj_id}")
        log(f"add empty spaces: {copys}")
        if use_log:
            log(f"delete finished (id: {obj_id})(tag: {tag_dict[obj_id]}): {write_dict[obj_id]}")
        write_dict[obj_id] = []
        print_empty_spaces(empty_spaces)


def write_method_1(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use the same size space that belongs to the same tag
    ensure left_copy_num == 0

    Args:
        obj_id (int): id
        obj_size (int): size
        obj_tag (int): tag
        wo (WriteObjetc): wo
    """
    if not empty_spaces[obj_tag][obj_size]:
        return left_copy_num

    # copy: size, index, pointer
    if use_log:
        log(f"write method 1")
        print_empty_spaces(empty_spaces)
    copys = empty_spaces[obj_tag][obj_size].pop()

    for c in range(1, COPY_NUM + 1):
        wo.write_disk_serial[c] = copys[c - 1][3]
        wo.write_position[c] = copys[c - 1][2]

        write_dict[obj_id].append(copys[c - 1])
        
        record_disk(obj_id, obj_size, wo.write_disk_serial[c], wo.write_position[c])
        left_copy_num -= 1
    return left_copy_num


def write_method_2(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use pre-allocated space, change the bound
    """
    if left_copy_num == 0:
        return left_copy_num
    
    use_method_2 = False
    for c in range(1, COPY_NUM+1):
        if write_bounds[obj_tag][c][0] + obj_size >= write_bounds[obj_tag][c][1]:
            continue
        
        index = write_index[obj_tag][c]
        if index in wo.write_disk_serial:
            continue
        copy_serial = COPY_NUM - left_copy_num + 1
        
        use_method_2 = True
        position = write_bounds[obj_tag][c][0]

        write_bounds[obj_tag][c][0] += obj_size
        
        wo.write_disk_serial[copy_serial] = index
        wo.write_position[copy_serial] = position
        record_disk(obj_id, obj_size, index, position)
        write_dict[obj_id].append([obj_tag, obj_size, position, index])
        
        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num
        
    if use_log and use_method_2:
        log(f"write method 2")
    return left_copy_num


def write_method_3(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use the empty space (released) that is larger than the object size
    ensure left_copy_num = 0
    Returns:
        exist_enough_space(bool): 
    """
    # use other empty space
    if left_copy_num == 0:
        return left_copy_num
    
    use_method_3 = False
    for i in range(len(empty_spaces[obj_tag]) - 1, obj_size, -1):
        if not empty_spaces[obj_tag][i]:
            continue
        use_method_3 = True
        copys = empty_spaces[obj_tag][i].pop()

        tmp_list = []
        for c in range(1, COPY_NUM + 1):
            wo.write_disk_serial[c] = copys[c - 1][3]
            wo.write_position[c] = copys[c - 1][2]

            copys[c - 1][1] -= obj_size  # space used, left size
            copys[c - 1][2] += obj_size  # position increased

            record_disk(obj_id, obj_size, wo.write_disk_serial[c], wo.write_position[c])

            write_dict[obj_id].append(copys[c - 1])
            
            tmp_list.append(copys[c - 1])
            left_copy_num -= 1
            
        if copys[-1][1]:
            log(f"current id: {obj_id}, current size: {obj_size}, current tag: {obj_tag}")
            log(f"add empty spaces: {tmp_list}")
            empty_spaces[obj_tag][copys[-1][1]].append(tmp_list)
        break
    
    if use_method_3 and use_log:
        log("write_method_3")
        log("out of bound use former empty space or other spaces")
        print_empty_spaces(empty_spaces)

    return left_copy_num


def write_method_4(left_copy_num, obj_id, obj_size, obj_tag, wo):
    if left_copy_num == 0:
        return left_copy_num
    
    for i in range(1, N+1):
        if i not in tag_assignments[obj_tag]:
            continue
        
        if i in wo.write_disk_serial:
            continue
        
        assign_pos = tag_assignments[obj_tag].index(i)
        
        copy_serial = COPY_NUM - left_copy_num + 1
        if public_bounds[i][assign_pos] != [-1, -1]:
            postion = public_bounds[i][assign_pos][0]
            index = i
            public_bounds[i][assign_pos][0] += obj_size
            
        elif public_bounds[i][assign_pos-1] != [-1, -1]:
            postion = public_bounds[i][assign_pos-1][1]
            index = i
            public_bounds[i][assign_pos][1] -= obj_size
        else:
            continue
        
        wo.write_disk_serial[copy_serial] = index
        wo.write_position[copy_serial] = postion
        
        record_disk(obj_id, obj_size, index, postion)
        write_dict[obj_id].append([obj_tag, obj_size, postion, index])
        
        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num

    return left_copy_num


def write_method_5(left_copy_num, obj_id, obj_size, obj_tag, wo):
    # use the space (other tag) that is related to this tag
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"\nwrite method 5")
        log(f"obj_tag: {obj_tag}, ")
        
    for i in range(1, N + 1):
        if not obj_relation[i][obj_tag]:
            continue
        
        if i in wo.write_disk_serial:
            continue
        
        copy_serial = COPY_NUM - left_copy_num + 1
        
        if use_log:
            left_tag, right_tag = obj_relation[i][obj_tag]
            log(f"{i}")
            log(f"left tag: {left_tag}, right tag: {right_tag}")
            log(f"left tag bounds: {write_bounds[left_tag]}")
            log(f"right tag bounds: {write_bounds[right_tag]}")

        left_tag, right_tag = obj_relation[i][obj_tag]
        left_copy_serial = tag_assignments[left_tag].index(i)
        right_copy_serial = tag_assignments[right_tag].index(i)

        index, position = -1, -1
        if (write_bounds[left_tag][left_copy_serial][0] + obj_size < write_bounds[left_tag][left_copy_serial][1]):
            if tag_assignments[i][-1] == left_tag:
                continue
            
            index = i
            position = write_bounds[left_tag][left_copy_serial][1] - 1  - obj_size
            
            write_bounds[left_tag][left_copy_serial][1] -= obj_size
            
            write_dict[obj_id].append([obj_tag, obj_size, position, i])
            record_disk(obj_id, obj_size, index, position)
            
        elif (write_bounds[right_tag][right_copy_serial][0] + obj_size < write_bounds[right_tag][right_copy_serial][1]):
            if tag_assignments[i][1] == right_tag:
                continue
            
            index = i
            position = write_bounds[right_tag][right_copy_serial][0]
            
            write_bounds[right_tag][right_copy_serial][0] += obj_size
            
            write_dict[obj_id].append([obj_tag, obj_size, position, i])
            record_disk(obj_id, obj_size, index, position)
        else:
            continue
        
        wo.write_disk_serial[copy_serial] = index
        wo.write_position[copy_serial] = position
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if log: log(f"left_copy_num: {left_copy_num}")
            return left_copy_num
        
    if log: log(f"left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_6(left_copy_num, obj_id, obj_size, obj_tag, wo):
    if left_copy_num == 0:
        return left_copy_num
    
    
    for i in range(1, N + 1):
        copy_serial = COPY_NUM - left_copy_num + 1
        
        

def do_write_object(obj_id, obj_size, obj_tag):
    global write_dict, empty_spaces, used_spaces, disk
    wo = WriteOutput(obj_id, obj_size)
    left_copy_num = 3

    write_dict[obj_id] = []  # position, index
    # use released space first
    left_copy_num = write_method_1(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_2(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_3(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_4(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_5(left_copy_num, obj_id, obj_size, obj_tag, wo)
    
    wo.print_info()
    if left_copy_num:
        log_disk(disk, tag_dict)
        log(f"remaining copy num: {left_copy_num}")
        sys_break()
    
    if use_log:
        log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {wo.write_disk_serial}, position: {wo.write_position}")

    

def timestamp_action():
    global current_timestamp
    current_timestamp = input().split()[1]
    print(f"TIMESTAMP {current_timestamp}")
    if use_log:
        log(f"\nTIMESTAMP {current_timestamp}")
    sys.stdout.flush()


def pre_action():
    global T, M, N, V, G
    global delete_info, write_info, read_info
    global disk
    global tag_assignments, read_positions, read_requests
    global write_index, write_bounds, write_dict
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
        if use_log: log(f"try disk_cost: {disk_cost}")

        min_need_index = need_spaces.index(min(need_spaces))
        last_min_index = min_need_index
        last_min_value = finnal_cost_list[min_need_index]

        need_spaces[min_need_index] = V + 1
        if min(need_spaces) >= V * 0.10:
            # restore the value
            break

        finnal_cost_list[min_need_index] = max_cost_list[min_need_index]
        tmp_disk_assignments = copy.deepcopy(disk_assignments)

    if use_log:
        log(f"disk assignment: {disk_assignments}")

    allocate_spaces(finnal_cost_list, max_cost_list, disk_assignments)

    print("OK")
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
    for i in range(len(write_obj)):
        obj_id, obj_size, obj_tag = write_obj[i]
        tag_dict[obj_id] = obj_tag
        do_write_object(obj_id, obj_size, obj_tag)
        log("\n")

    sys.stdout.flush()
    if use_log:
        log("write finished")


def read_action():
    n_read, read_req_id, read_obj_id = read_input()
    for i in range(n_read):
        read_requests[read_obj_id[i]].append(read_req_id[i])

    for i in range(0, N):
        print("#")
    print("0")
    sys.stdout.flush()
