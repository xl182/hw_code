import copy
import sys
from typing import List
from algorithm import allocate_files, calc_occupy
from get_in import pre_input
from global_variables import g
from utils import *


def init_variables(T, M, N, V, G):
    if g.use_write_log:
        log(f"T, M, N, V, G: {T, M, N, V, G}")

    g.disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    g.empty_spaces = [
        [[] for i in range(g.MAX_OBJ_SIZE)] for _ in range(M + 1)
    ]  # [[[] * size] * M + 1]

    g.write_index = [
        [0 for _ in range(g.COPY_NUM + 1)] for i in range(M + 1)
    ]  # volume index of each tag
    g.write_bounds = [[[-1, -1] for j in range(g.COPY_NUM+1)] for i in range(M + 1)]
    # the used space of each volume
    g.obj_relation = [[[] for j in range(M + 1)] for i in range(N + 1)]

    g.free_empty_spaces = [[[] for j in range(g.MAX_OBJ_SIZE)] for i in range(N + 1)]
    g.left_allocate_sizes = [0 if i != 0 else 0 for i in range(N + 1)] 
    g.left_public_sizes = [0 if i != 0 else 0 for i in range(N + 1)]


def allocate_spaces(
    min_cost: List[int], max_cost: List[int], assignments: List[List[int]]
):
    if g.use_write_log:
        log(f"min_cost: {min_cost}, max_cost: {max_cost}")

    # sort space according to max_size - min_size, some may be 0
    diff_spaces = [[0] for i in range(g.N + 1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            diff_spaces[i].append(max_cost[assignments[i][j]] - min_cost[assignments[i][j]])
            
        zipped = zip(diff_spaces[i][1:], assignments[i][1:])
        sorted_zipped = sorted(zipped, key=lambda x: x[0], reverse=False)
        sz1, sz2 = zip(*sorted_zipped)
        diff_spaces[i][1:], assignments[i][1:] = list(sz1), list(sz2)
        
    if g.use_write_log:
        log(f"new assignments")
        log(f"diff spaces: {diff_spaces}")
        log(f"assignments: {assignments}")

    g.tag_assignments = [[0] for i in range(g.M + 1)]
    for i in range(1, len(assignments)):
        for j in range(1, len(assignments[i])):
            g.tag_assignments[assignments[i][j]].append(i)

            tag = assignments[i][j]
            last_tag = assignments[i][j - 1] if j != 1 else assignments[i][-1]
            next_tag = (assignments[i][j + 1] if j < len(assignments[i]) - 1 else assignments[i][1])
            g.obj_relation[i][tag] = [last_tag, next_tag]
            
    if g.use_write_log:
        log(f"obj_relation: {g.obj_relation}")
        log(f"tag assignments: {g.tag_assignments}")

    disk_cost = [0 for _ in range(g.N + 1)]
    for i in range(1, len(g.tag_assignments)):
        for j in range(1, g.COPY_NUM + 1):
            index = g.tag_assignments[i][j]
            disk_cost[index] += min_cost[i]
    if g.use_write_log:
        log(f"disk cost: {disk_cost}, sum: {sum(disk_cost)}")

    weights = [[0 for j in range(len(assignments[i]))] if i != 0 else [0] for i in range(len(assignments))]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])):
            tag = assignments[i][j]
            weights[i][j] = diff_spaces[i][j - 1] + diff_spaces[i][j]

    g.public_sizes = [[0 for j in range(len(assignments[i]))] if i != 0 else [0]for i in range(len(assignments))]
    g.public_bounds = [[[0, 0] for j in range(len(assignments[i]))] if i != 0 else [[-1]] for i in range(len(assignments))]
    free_sizes = [g.V - disk_cost[i] for i in range(g.N + 1)]
    for i in range(1, len(assignments)):
        for j in range(2, len(assignments[i])-1):
            if sum(weights[i]) != 0:
                g.public_sizes[i][j] = int(free_sizes[i] * weights[i][j] / (sum(weights[i])))
        g.public_sizes[i][-1] = free_sizes[i] - sum(g.public_sizes[i]) - 2
        
    if g.use_write_log:
        log(f"public sizes: {g.public_sizes}")

    volume_positions = [1 for i in range(g.N + 1)]
    copy_serial = [0 for _ in range(g.M + 1)]
    for i in range(1, len(assignments)):
        positive_num = sum(i > 0 for i in g.public_sizes[i])
        for j in range(1, len(assignments[i])):
            tag = assignments[i][j]
            copy_serial[tag] += 1

            g.write_index[tag][copy_serial[tag]] = i
            g.write_bounds[tag][copy_serial[tag]][0] = volume_positions[i]
            volume_positions[i] += min_cost[tag]
            g.left_allocate_sizes[i] += min_cost[tag]  # record write bounds sizes of each volume
            g.write_bounds[tag][copy_serial[tag]][1] = volume_positions[i]

            if (g.public_sizes[i][j] > 0 and j != len(assignments[i]) - 1 and positive_num != 1): 
                g.public_bounds[i][j][0] = volume_positions[i]
            if positive_num == 1 and j == len(assignments[i]) - 2:
                g.public_bounds[i][j][0] = volume_positions[i]
            volume_positions[i] += g.public_sizes[i][j]
            g.left_public_sizes[i] += g.public_sizes[i][j]

            if (g.public_sizes[i][j] > 0 and j != len(assignments[i]) - 1 and positive_num != 1):
                g.public_bounds[i][j][-1] = volume_positions[i]

            if j == len(assignments[i]) - 2:
                volume_positions[i] += g.public_sizes[i][j + 1]
                g.left_public_sizes[i] += g.public_sizes[i][j + 1]
                if g.public_sizes[i][j] > 0 or positive_num == 1:
                    g.public_bounds[i][j][-1] = volume_positions[i]

    if g.use_write_log:
        log(f"public bounds: {g.public_bounds}")
        log(f"new public sizes: {g.public_sizes}")
        log(f"write_index: {g.write_index}")
        log(f"write_bounds: {g.write_bounds}")



def pre_action():
    para, info = pre_input()

    g.T, g.M, g.N, g.V, g.G = para
    init_variables(g.T, g.M, g.N, g.V, g.G)

    # calc the min cost of each tag, info index start from 1, finnal_cost_list also means min_cost_list
    g.delete_info, g.write_info, g.read_info = info
    finnal_cost_list, max_cost_list = calc_occupy(g.write_info, g.delete_info, g.M)
    if g.use_write_log:
        log(f"final: {finnal_cost_list}, max: {max_cost_list}")

    need_spaces = [
        max_cost_list[i] - finnal_cost_list[i] for i in range(len(finnal_cost_list))
    ]
    need_spaces[0] = g.V + 1
    # try to find the min need space that is not 0
    while min(need_spaces) == 0:
        min_need_index = need_spaces.index(min(need_spaces))
        need_spaces[min_need_index] = g.V + 1

    # try to increase the size of finnal_cost_list
    tmp_disk_assignments = None
    last_min_index, last_min_value = 0, 0
    while True:
        g.disk_assignments, split_files = allocate_files(finnal_cost_list, g.N, g.V)  # vloume
        if not g.disk_assignments:
            g.disk_assignments = tmp_disk_assignments

            # restore the value
            finnal_cost_list[last_min_index] = last_min_value
            break
        disk_cost = [0 for _ in range(g.N + 1)]
        for i in range(1, len(g.disk_assignments)):
            for j in range(1, len(g.disk_assignments[i])):
                tag = g.disk_assignments[i][j]
                disk_cost[i] += finnal_cost_list[tag]
        if max(disk_cost) > g.V:
            g.disk_assignments = tmp_disk_assignments
            break
        if g.use_write_log: log(f"try disk_cost: {disk_cost}")

        min_need_index = need_spaces.index(min(need_spaces))
        last_min_index = min_need_index
        last_min_value = finnal_cost_list[min_need_index]

        need_spaces[min_need_index] = g.V + 1
        if min(need_spaces) >= g.V * 0.10:
            # restore the value
            break

        finnal_cost_list[min_need_index] = max_cost_list[min_need_index]
        tmp_disk_assignments = copy.deepcopy(g.disk_assignments)

    if g.use_write_log:
        log(f"disk assignment: {g.disk_assignments}")

    allocate_spaces(finnal_cost_list, max_cost_list, g.disk_assignments)

    print("OK")
    sys.stdout.flush()
    return g.T, g.M, g.N, g.V, g.G
