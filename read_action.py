from copy import deepcopy
import inspect
import math
from re import DEBUG
from get_in import read_input
from global_variables import g

import bisect

from output import ReadOutput
from utils import CRITICAL, ERROR, WARN, log

c_frame = inspect.currentframe


def find_larger_pos(src_list, value):
    """
    if value is larger than the last element of src_list, return -1
    else return the index of the first element in src_list that is larger than value
    """
    pos = bisect.bisect_right(src_list, value)
    if pos >= len(src_list):
        return -1
    return pos


def set_request_volume(obj_id, volume_index):
    if obj_id == 0:
        return
    log(
        f"set request volume: id: {obj_id}, index: {volume_index}, request id: {g.request_id_dict[obj_id]}",
        c_frame=c_frame(),
    )
    copys = g.write_dict[obj_id]

    for copy in copys:
        tag, size, pos, index = copy
        id_index = g.request_data_list[index].id_list.index(obj_id)
        g.request_data_list[index].remove(id_index)
        g.left_read_size[volume_index] = size
    g.current_read_obj[volume_index] = obj_id


def do_jump(i, left_token, next_position, ro):
    ro.add_jump(i, next_position)
    g.current_neddle[i] = next_position
    g.if_last_read[i] = False
    g.last_read_cost[i] = g.BASE_READ_COST
    left_token[i] = 0


def do_pass(i, left_token, pass_size, ro: ReadOutput):
    if pass_size >= g.G:
        return
    g.if_last_read[i] = False
    g.last_read_cost[i] = g.BASE_READ_COST
    if left_token[i] >= pass_size:
        g.left_pass_size[i] = 0
        ro.add_pass(i, pass_size)
        g.current_neddle[i] += pass_size
        left_token[i] -= pass_size
    else:
        g.left_pass_size[i] = pass_size - left_token[i]
        ro.add_pass(i, left_token[i])
        g.current_neddle[i] += left_token[i]
        left_token[i] = 0


def do_read(index, left_token, read_size, ro: ReadOutput):
    if read_size == 0:
        return

    for s in range(0, read_size):
        if g.if_last_read[index]:
            cost = max(math.ceil(g.last_read_cost[index] * 0.8), 16)
        else:
            cost = g.BASE_READ_COST

        if left_token[index] < cost:
            return
        log(f"read_position: {g.current_neddle[index]}", c_frame=c_frame())

        ro.add_read(index)
        g.left_read_size[index] -= 1
        g.if_last_read[index] = True
        g.last_read_cost[index] = cost
        left_token[index] -= cost
        g.current_neddle[index] += 1
        if g.current_neddle[index] == g.V + 1:
            g.current_neddle[index] = 1

    # read finished
    obj_id = g.current_read_obj[index]
    g.current_read_obj[index] = 0

    ro.add_finished_request(g.request_id_dict[obj_id])
    ro.finished_request = []
    g.request_id_dict[obj_id] = deepcopy(g.new_id_dict[obj_id])


def calc_distance(position, current_position):
    if position >= current_position:
        return position - current_position
    else:
        return g.V - current_position + position


def read_action():
    n_read, read_req = read_input()
    ro = ReadOutput(g.N)

    for req_id, obj_id in read_req[:n_read]:
        g.request_id_dict[obj_id].append(req_id)
        g.new_id_dict[obj_id].append(req_id)
        copys = g.write_dict[obj_id]

        for copy in copys:
            tag, size, pos, index = copy
            timestamp = g.current_timestamp
            g.request_data_list[index].insert([pos, size, obj_id, timestamp, tag])

    # left_size = sum([sum(g.request_id_dict[i]) for i in range(len(g.request_id_dict))])
    # log(f"left size: {left_size}", mode=ERROR, c_frame=c_frame())

    left_token = [g.G for i in range(g.N + 1)]
    # selected_list = [i for i in range(g.N + 1)]
    # request_size = [
    #     len(g.request_data_list[i].pos_list) for i in range(len(g.request_data_list))
    # ]
    # request_size[0] = g.V + 1
    # combined = list(zip(request_size, selected_list))
    # sorted_combined = sorted(combined, key=lambda x: x[0])
    # request_size, selected_list = zip(*sorted_combined)

    request_size = [
        g.V + 1 if i == 0 else len(g.request_data_list[i].pos_list)
        for i in range(len(g.request_data_list))
    ]
    sorted_indices = sorted(range(len(request_size)), key=lambda i: request_size[i])
    request_size = [request_size[i] for i in sorted_indices]
    selected_list = sorted_indices
    for i in selected_list[:-1]:
        log(f"current index: {i}", mode=DEBUG, new_line=True, c_frame=c_frame())
        log(
            f"left pass size: {g.left_pass_size[i]}, left read size: {g.left_read_size[i]}",
            c_frame=c_frame(),
        )
        g.id_dict_locked[i] = False
        count = 0
        while True:
            count += 1
            log(f"loop count: {count}")
            # read the left size
            if g.left_read_size[i]:
                if count == 1:
                    g.id_dict_locked[i] = True
                do_read(i, left_token, g.left_read_size[i], ro)
                if g.left_read_size[i]:
                    break

            if g.left_pass_size[i]:
                do_pass(i, left_token, g.left_pass_size[i], ro)
                if g.left_pass_size[i]:
                    break
                set_request_volume(g.current_read_obj[i], i)
                do_read(i, left_token, g.left_read_size[i], ro)
                log(
                    f"left pass size: {g.left_pass_size[i]}, left read size: {g.left_read_size[i]}",
                    c_frame=c_frame(),
                )
            if len(g.request_data_list[i].pos_list) == 0:
                break

            # find the next obj to read, and move to the next position
            next_position_index = find_larger_pos(
                g.request_data_list[i].pos_list, g.current_neddle[i]
            )
            pos, size, obj_id, timestamp, tag = g.request_data_list[i].data_list[
                next_position_index
            ]

            next_position = g.request_data_list[i].pos_list[next_position_index]
            # if next position is not in the latter position then jump to the first position
            if (
                next_position_index == -1
                and g.request_data_list[i].pos_list[-1] != g.current_neddle[i]
                and left_token[i] == g.G
            ):
                log(
                    f"next position is not in the latter position then jump to the first position {g.request_data_list[i].pos_list[0]}"
                    f"left_token: {left_token[i]}, do jump",
                    c_frame=c_frame(),
                )
                next_obj_id = g.request_data_list[i].data_list[0][2]
                do_jump(i, left_token, g.request_data_list[i].pos_list[0], ro)
                set_request_volume(next_obj_id, i)
                break
            # if next position is in the latter position then move to the next position
            pass_size = calc_distance(next_position, g.current_neddle[i])

            # if pass_size is larger than the token, then jump to the next position
            log(
                f"pass size: {pass_size}, left_token: {left_token[i]}",
                c_frame=c_frame(),
            )
            if pass_size >= g.G:
                if left_token[i] == g.G:
                    log(
                        f"left token: {left_token[i]}, jump to next position",
                        c_frame=c_frame(),
                    )
                    do_jump(i, left_token, next_position, ro)
                    set_request_volume(obj_id, i)
                    log(
                        f"pass_size is larger than the token, then jump to the ",
                        c_frame=c_frame(),
                    )
                    log(f"jump to next position: {next_position}", c_frame=c_frame())
                    log(f"current obj: {g.current_read_obj[i]}", c_frame=c_frame())
                    break
                if pass_size >= g.G + left_token[i] - g.BASE_READ_COST:
                    break

            do_pass(i, left_token, pass_size, ro)
            # pass to the next position
            log(
                f"do pass to next position: {next_position}, pass size: {pass_size}, index: {i}, left_token: {left_token[i]}",
                c_frame=c_frame(),
            )

            if g.left_pass_size[i]:
                break

            set_request_volume(obj_id, i)
            do_read(i, left_token, size, ro)
            if left_token[i] == 0:
                break

    ro.print_info()


# def calc_volume(left_token, ro):
#     for i in range(1, g.N + 1):
#         if g.volume_locked[i]:
#             continue

#         if len(g.request_data_list[i].pos_list) < 10:
#             continue

#         scores = [0 for i in range(len(g.request_data_list[i].pos_list))]
#         for j in range(len(g.request_data_list[i].pos_list)):
#             pos, size, obj_id, timestamp, tag = g.request_data_list[i].data_list[j]
#             x = g.current_timestamp - timestamp
#             if x < 10:
#                 k = 0.0005 * x
#             else:
#                 k = 0.01
#             scores[i] = (1.05 - x * k) * (1 + size) / 2
#         dense_regions, _ = find_dense_regions_with_weights(
#             g.request_data_list[i].pos_list, scores
#         )
#         if not dense_regions:
#             continue

#         # find the largest dense region
#         min_distance = g.V + 1
#         min_index = -1
#         for d in range(len(dense_regions)):
#             if dense_regions[d][0] - g.current_neddle[i] < 0:
#                 continue
#             if dense_regions[d][0] - g.current_neddle[i] < min_distance:
#                 min_distance = dense_regions[d][0] - g.current_neddle[i]
#                 min_index = i
#         near_region = dense_regions[min_index]
#         max_region = max(dense_regions, key=len)

#         if max_region == near_region:
#             g.volume_locked[i] = True
#             g.waiting_reading_area[0] = find_larger_pos(
#                 near_region, g.current_neddle[i]
#             )
#             g.waiting_reading_area[i] = near_region[-1]
#         else:
#             max_region_decay_sum = 0
#             start_index = g.request_data_list[i].pos_list.index(max_region[0])
#             for j in range(len(max_region)):
#                 pos, size, obj_id, timestamp, tag = g.request_data_list[i].data_list[
#                     start_index + j
#                 ]
#                 x = g.current_timestamp - timestamp
#                 if x < 10:
#                     k = 0.0005 * x
#                 else:
#                     k = 0.01
#                 max_region_decay_sum += x * k * (1 + size) / 2

#             near_region_decay_sum = 0
#             start_index = g.request_data_list[i].pos_list.index(near_region[0])
#             for j in range(len(near_region)):
#                 pos, size, obj_id, timestamp, tag = g.request_data_list[i].data_list[
#                     start_index + j
#                 ]
#                 x = g.current_timestamp - timestamp
#                 if x < 10:
#                     k = 0.0005 * x
#                 else:
#                     k = 0.01
#                 near_region_decay_sum += x * k * (1 + size) / 2

#             if max_region_decay_sum - near_region_decay_sum > g.G / 50:
#                 g.volume_locked[i] = True
#                 g.waiting_reading_area[0] = find_larger_pos(
#                     max_region, g.current_neddle[i]
#                 )
#                 g.waiting_reading_area[i] = max_region[-1]
#                 if (
#                     g.waiting_reading_area[0] - g.current_neddle[i]
#                     < g.G - g.BASE_READ_COST
#                 ):
#                     for i in range(g.waiting_reading_area[0] - g.current_neddle[i]):
#                         ro.add_action(i, g.PASS)
#                     left_token[i] = g.G - (
#                         g.waiting_reading_area[0] - g.current_neddle[i]
#                     )
#                 else:
#                     ro.add_jump(i, g.waiting_reading_area[0])
#                     left_token[i] = 0
#             else:
#                 g.volume_locked[i] = True
#                 g.waiting_reading_area[0] = find_larger_pos(
#                     near_region, g.current_neddle[i]
#                 )
#                 g.waiting_reading_area[i] = near_region[-1]
