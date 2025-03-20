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
    
with open("log_test.log", "w") as f:
    pass

tag_assignments: Any  # [volume index] the assignments of each tag
disk_assignments: Any  # [tag] the assignments of each disk

delete_info: list
write_info: list
read_info: list

write_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
resorted_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
preempted_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
write_index: List[List[int]]  # [volume_index * 3] * M
write_cost: List[int]  # [size(int)]  the min cost of each tag

write_dict: List[List[int]]  # [obj_tag, obj_size, position, index]
dist: List  # simulate the disk

empty_spaces: List[List[List[int]]]  # [(size, disk, pointer)] * M
obj_relation: List[List[List[int]]]  # [[[left tag, right tag] * tag] * N]
# [[[size, [left pointer, right pointer], [left tag, right tag,] [left bound, right bound]] * tag] * N]
free_empty_spaces: Any  # [(size, disk, pointer)] * M
public_bounds: List[List[List[int]]]  # [left bound, right bound] * ? * ?
public_sizes: List[List[int]]
volume_left_spaces: List[int]  # [used_size * N], the used space of each volume
fragmented_spaces: List

read_requests: List[List[int]]  # [obj_id] * MAX_REQUEST_NUM id
current_needle: List[int]  # [position] * (N + 1)

disk: List

# init
COPY_NUM = 3
MAX_OBJECT_NUM = 100000 + 1
MAX_REQUEST_NUM = 30000000 + 1  # maximum number of requests
EXTRA_TIME = 105
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
    global write_index, write_bounds, volume_left_spaces, preempted_bounds, resorted_bounds, free_empty_spaces

    disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    read_positions = []
    empty_spaces = [
        [[] for i in range(max_obj_size)] for _ in range(M + 1)
    ]  # [[[] * size] * M + 1]
    used_spaces = [0 for _ in range(N + 1)]

    write_index = [
        [0 for _ in range(COPY_NUM + 1)] for i in range(M + 1)
    ]  # volume index of each tag
    write_bounds = [[[-1, -1] for j in range(COPY_NUM+1)] for i in range(M + 1)]
    preempted_bounds = [[[-1, -1] for j in range(COPY_NUM+1)] for i in range(M + 1)]
    # the used space of each volume
    obj_relation = [[[] for j in range(M + 1)] for i in range(N + 1)]
    volume_left_spaces = [V for i in range(N)]  # the left space of each volume
    volume_left_spaces.insert(0, 0)
    
    free_empty_spaces = [[[] for j in range(max_obj_size)] for i in range(N + 1)]


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
        [0 for j in range(len(assignments[i]))] if i != 0 else [0]
        for i in range(len(assignments))
    ]
    public_bounds = [
        [[0, 0, 0, 0] for j in range(len(assignments[i]))] if i != 0 else [[-1]]
        for i in range(len(assignments))
    ]
    free_sizes = [V - disk_cost[i] for i in range(N + 1)]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])-1):
            if sum(weights[i]) != 0:
                public_sizes[i][j] = int(free_sizes[i] * weights[i][j] / (sum(weights[i])))
        public_sizes[i][-1] = free_sizes[i] - sum(public_sizes[i]) - 2
        
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
                public_bounds[i][j][-1] = volume_positions[i]

            if j == len(assignments[i]) - 2:
                volume_positions[i] += public_sizes[i][j + 1]
                if public_sizes[i][j] > 0 or positive_num == 1:
                    public_bounds[i][j][-1] = volume_positions[i]
            public_bounds[i][j][1] = (public_bounds[i][j][0] + public_bounds[i][j][-1]) // 2
            public_bounds[i][j][2] = public_bounds[i][j][1] + 1
            
    resorted_bounds = [[] for i in range(1, 12)]
    if use_log:
        log(f"{len(tag_assignments)}")
    for i in range(1, 17):
        for j in range(1, 4):
            resorted_bounds[tag_assignments[i][j]].append(write_bounds[i][j])
    if use_log:
        log(f"resorted_bounds: {resorted_bounds}")
    
    rate = 3 / 5
    for i in range(1, len(write_bounds)):
        for j in range(1, len(write_bounds[i])):
            preempted_bounds[i][j][0] = int(write_bounds[i][j][0] + rate * (write_bounds[i][j][1] - write_bounds[i][j][0]))
            preempted_bounds[i][j][1] = preempted_bounds[i][j][0] + 1

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
            for s in range(size):
                disk[index][pos + s] = -1
            volume_left_spaces[index] += size
            
        tag, size, pos, index = copys[0]
        empty_spaces[tag][size].append(copys)
        write_dict[obj_id] = []
        if use_log:
            log(f"delete current id: {obj_id}")
            log(f"add empty spaces: {copys}")
            log(f"delete finished (id: {obj_id})(tag: {tag_dict[obj_id]}): {write_dict[obj_id]}")
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
        wo.disk_serial[c] = copys[c - 1][3]
        wo.position[c] = copys[c - 1][2]

        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num
        
    return left_copy_num


def write_method_2(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use pre-allocated space, change the bound
    """
    if left_copy_num == 0:
        return left_copy_num
    
    use_method_2 = False
    for c in range(1, COPY_NUM+1):
        if write_bounds[obj_tag][c][0] + obj_size > write_bounds[obj_tag][c][1]:
            continue
        
        index = write_index[obj_tag][c]
        if index in wo.disk_serial:
            continue
        copy_serial = COPY_NUM - left_copy_num + 1
        
        use_method_2 = True
        position = write_bounds[obj_tag][c][0]

        write_bounds[obj_tag][c][0] += obj_size
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = position
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if use_log and use_method_2:
                log(f"write method 2")
            return left_copy_num
        
    if use_log and use_method_2:
        log(f"write method 2")
    if use_log:
        log(f"2 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_3(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use the empty space (released) that is larger than the object size
    ensure left_copy_num = 0
    Returns:
        exist_enough_space(bool): 
    """
    # use other empty space
    if left_copy_num != 3:
        return left_copy_num
    
    use_method_3 = False
    for i in range(len(empty_spaces[obj_tag]) - 1, obj_size, -1):
        if not empty_spaces[obj_tag][i]:
            continue
        use_method_3 = True
        copys = empty_spaces[obj_tag][i].pop()

        tmp_list = []
        for c in range(1, COPY_NUM + 1):
            wo.disk_serial[c] = copys[c - 1][3]
            wo.position[c] = copys[c - 1][2]

            copys[c - 1][1] -= obj_size  # space used, left size
            copys[c - 1][2] += obj_size  # position increased
            
            tmp_list.append(copys[c - 1])
            left_copy_num -= 1
            if left_copy_num == 0:
                return left_copy_num
            
        if copys[-1][1]:
            if use_log:
                log(f"current id: {obj_id}, current size: {obj_size}, current tag: {obj_tag}")
                log(f"add empty spaces: {tmp_list}")
            empty_spaces[obj_tag][copys[-1][1]].append(tmp_list)
        break
    
    if use_method_3 and use_log:
        log("\nwrite_method 3")
        log("out of bound use former empty space or other spaces")
        print_empty_spaces(empty_spaces)
    return left_copy_num


def write_method_4(left_copy_num, obj_id, obj_size, obj_tag, wo):
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"write method 4")
        log(f"left_copy_num: {left_copy_num}")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    for i in tag_assignments[obj_tag][1:]:
        if i in wo.disk_serial:
            continue
        assign_pos = disk_assignments[i].index(obj_tag)
        copy_serial = COPY_NUM - left_copy_num + 1
        if use_log:
            log(f"index: {i}, {public_bounds[i][assign_pos]}: {public_bounds[i][assign_pos-1]}, ")
        
        if public_bounds[i][assign_pos][0] + obj_size <= public_bounds[i][assign_pos][-1]:
            postion = public_bounds[i][assign_pos][0]
            index = i
            public_bounds[i][assign_pos][0] += obj_size
            
        elif public_bounds[i][assign_pos-1][0] + obj_size <= public_bounds[i][assign_pos-1][-1]:
            postion = public_bounds[i][assign_pos-1][-1] - obj_size
            index = i
            public_bounds[i][assign_pos-1][-1] -= obj_size
        else:
            continue
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = postion
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if use_log:
                log(f"method 4: left_copy_num: {left_copy_num}")
            return left_copy_num
    if use_log:
        log(f"4 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_5(left_copy_num, obj_id, obj_size, obj_tag, wo):
    # use the space (other tag) that is related to this tag
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"write method 5")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    for i in range(1, N + 1):
        if not obj_relation[i][obj_tag]:
            continue
        
        if i in wo.disk_serial:
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
        if (write_bounds[left_tag][left_copy_serial][0] + obj_size <= write_bounds[left_tag][left_copy_serial][1]):
            if tag_assignments[i][-1] == left_tag:
                continue
            
            index = i
            position = write_bounds[left_tag][left_copy_serial][1] - obj_size
            
            write_bounds[left_tag][left_copy_serial][1] -= obj_size
            
        elif (write_bounds[right_tag][right_copy_serial][0] + obj_size <= write_bounds[right_tag][right_copy_serial][1]):
            if tag_assignments[i][1] == right_tag:
                continue
            
            index = i
            position = write_bounds[right_tag][right_copy_serial][0]
            
            write_bounds[right_tag][right_copy_serial][0] += obj_size
        else:
            continue
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = position
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if use_log: log(f"5 left_copy_num: {left_copy_num}")
            return left_copy_num
        
    if use_log: log(f"5 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_6(left_copy_num, obj_id, obj_size, obj_tag, wo):
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"write method 6")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        log(f"left_copy_num: {left_copy_num}")
        
    free_sizes = [0 for i in range(N+1)]
    for i in range(1, 1+N):
        # i : volume index
        if i in wo.disk_serial:
            continue
        copy_serial = COPY_NUM - left_copy_num + 1

        diff_list = [0 for _ in range(len(disk_assignments[i]))]
        tag_list = disk_assignments[i]  # tag list in this volume
        
        for t, tag in enumerate(tag_list[1:]):
            tag_copy_serial = tag_assignments[tag].index(i)
            diff_list[t+1] = write_bounds[tag][tag_copy_serial][-1] - write_bounds[tag][tag_copy_serial][0]
        free_sizes[i] = sum(diff_list)
    if max(free_sizes) < obj_size:
        return left_copy_num

    top_indices = sorted(range(len(free_sizes)), key=lambda i: free_sizes[i], reverse=True)
    if use_log:
        log(f"obj_id: {obj_id}")
        log(f"free spaces: {free_sizes}")
        log(f"top indices: {top_indices}")
        
    for i in top_indices:
        # i : volume index
        if i in wo.disk_serial or i == 0:
            continue
        copy_serial = COPY_NUM - left_copy_num + 1

        diff_list = [0 for _ in range(len(disk_assignments[i]))]
        tag_list = disk_assignments[i]  # tag list in this volume
        
        for t, tag in enumerate(tag_list[1:]):
            tag_copy_serial = tag_assignments[tag].index(i)
            diff_list[t+1] = write_bounds[tag][tag_copy_serial][-1] - write_bounds[tag][tag_copy_serial][0]
        
        if max(diff_list) < obj_size:
            return left_copy_num
        
        top_tag_index = diff_list.index(max(diff_list))  # the index of max_size
        tag = tag_list[top_tag_index]
        tag_copy_serial = tag_assignments[tag].index(i)
        
        if use_log:
            log(f"tag_list: {tag_list}")
            log(f"diff_list: {diff_list}")
            log(f"tag: {tag}, tag_copy_serial: {tag_copy_serial}")
            log(f"tag bounds: {write_bounds[tag]}")
        
        wo.disk_serial[copy_serial] = i
        wo.position[copy_serial] = write_bounds[tag][tag_copy_serial][0]
        write_bounds[tag][tag_copy_serial][0] += obj_size

        
        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num
        
    return left_copy_num
        
        
def write_method_7(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use public space of other tags

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_

    Returns:
        _type_: _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"write method 7")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
    
    public_bounds_sizes = [[0 for j in range(len(public_bounds[i]))] for i in range(N+1)]
    public_bounds_size_sum = [0 for i in range(N+1)]
    for i in range(1, N+1):
        for j in range(1, len(public_bounds[i])):
            public_bounds_sizes[i][j] += public_bounds[i][j][-1] - public_bounds[i][j][0]
        public_bounds_size_sum[i] = sum(public_bounds_sizes[i])
    top_indices = sorted(range(1, N+1), key=lambda i: public_bounds_size_sum[i], reverse=True)
    
    if use_log:
        log(f"public bounds sizes: {public_bounds_sizes}")
        log(f"public_bounds_size_sum: {public_bounds_size_sum}")
    
    for i in top_indices:
        if i in wo.disk_serial:
            continue
        
        if max(public_bounds_sizes[i]) < obj_size:
            continue
        
        copy_serial = COPY_NUM - left_copy_num + 1
        
        index = public_bounds_sizes[i].index(max(public_bounds_sizes[i]))
        position = public_bounds[i][index][0]
        
        wo.disk_serial[copy_serial] = i
        wo.position[copy_serial] = position
        public_bounds[i][index][0] += obj_size
        
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if use_log:
                log(f"7 left_copy_num: {left_copy_num}")
            return left_copy_num
    if use_log:
        log(f"7 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_8(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use empty spaces of other tags

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if use_log:
        log(f"write method 8")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    if use_log:
        log("use empty spaces of other tags of same size")
    for t in range(1, 1+M):
        # t : tag
        if t == obj_tag:
            continue
        if not empty_spaces[t][obj_size]:
            continue
        
        copys = empty_spaces[t][obj_size].pop()
        for c in range(1, COPY_NUM + 1):
            copy_serial = COPY_NUM - left_copy_num + 1
            index, position = copys[c - 1][3], copys[c - 1][2]
            
            if index in wo.disk_serial or left_copy_num == 0:
                free_empty_spaces[index][obj_size].append(copys[c - 1])
                continue
            
            wo.disk_serial[copy_serial] = index
            wo.position[copy_serial] = position
            left_copy_num -= 1
            
        if left_copy_num == 0:
            log(f"8 left_copy_num: {left_copy_num}")
            return left_copy_num
        
    if use_log:
        log("use larger empty spaces")
        print_empty_spaces(empty_spaces)
    for t in range(1, 1+M):
        # t : tag
        if t == obj_tag:
            continue

        copy_serial = COPY_NUM - left_copy_num + 1
        for s in range(max_obj_size - 1, obj_size, -1):
            if not empty_spaces[t][s]:
                continue
            copys = empty_spaces[t][s].pop()

            for c in range(1, COPY_NUM + 1):
                index, position = copys[c - 1][3], copys[c - 1][2] # type: ignore
                
                if left_copy_num == 0 or index in wo.disk_serial:
                    free_empty_spaces[index][copys[c - 1][1]].append(copys[c - 1]) # type: ignore
                    continue
                
                wo.disk_serial[copy_serial] = index
                wo.position[copy_serial] = position

                copys[c - 1][1] -= obj_size  # type: ignore # space used, left size
                copys[c - 1][2] += obj_size  # type: ignore # position increased
                free_empty_spaces[index][copys[c - 1][1]].append(copys[c - 1]) # type: ignore
                
                left_copy_num -= 1
    if use_log:
        log(f"8 left_copy_num: {left_copy_num}")
    return left_copy_num




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
    left_copy_num = write_method_6(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_7(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_8(left_copy_num, obj_id, obj_size, obj_tag, wo)
    
    for c in range(1, COPY_NUM + 1):
        index = wo.disk_serial[c]
        volume_left_spaces[index] -= obj_size
    
    for i in range(1, COPY_NUM + 1):
        index, position = wo.disk_serial[i], wo.position[i]
        write_dict[obj_id].append([obj_tag, obj_size, position, index])
    wo.print_info(disk)
    
    if left_copy_num:
        log_disk(disk, tag_dict)
        log(f"remaining copy num: {left_copy_num}")
        sys_break()
    
    if use_log:
        log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {wo.disk_serial}, position: {wo.position}")


def timestamp_action():
    global current_timestamp, use_log
    current_timestamp = input().split()[1]
    print(f"TIMESTAMP {current_timestamp}")
    if int(current_timestamp) == T+EXTRA_TIME:
        use_log = True
        log_disk(disk, tag_dict)
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
