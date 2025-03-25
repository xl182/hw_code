from copy import deepcopy
import bisect
import inspect
import math
from get_in import read_input

from output import ReadOutput
from utils import rt, ERROR, log
from global_variables import g

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
    copys = g.write_dict[obj_id]
    tag, size, pos, index = copys[0]

    read_position = -1
    for copy in copys:
        tag, size, pos, index = copy
        if index == volume_index:
            read_position = pos
        id_index = g.request_data_list[index].obj_id_list.index(obj_id)
        g.request_data_list[index].remove(id_index)
    g.left_read_size[volume_index] = size
    g.current_read_obj[volume_index] = obj_id

    log(
        f"set request volume obj_id: {obj_id}, index: {volume_index}, position: {read_position}",
        c_frame=c_frame(),
    )


def do_jump(i, left_token, next_position, ro):
    ro.add_jump(i, next_position)
    g.current_neddle[i] = next_position
    g.if_last_read[i] = False
    g.last_read_cost[i] = g.BASE_READ_COST
    left_token[i] = 0


def do_pass(i, left_token, ro: ReadOutput):
    g.if_last_read[i] = False
    g.last_read_cost[i] = g.BASE_READ_COST
    if left_token[i] >= g.left_pass_size[i]:
        ro.add_pass(i, g.left_pass_size[i])
        g.current_neddle[i] += g.left_pass_size[i]
        left_token[i] -= g.left_pass_size[i]
        g.left_pass_size[i] = 0
        log(f"pass to the next position: {g.current_neddle[i]}", c_frame=c_frame())
    else:
        g.left_pass_size[i] = g.left_pass_size[i] - left_token[i]
        ro.add_pass(i, left_token[i])
        g.current_neddle[i] += left_token[i]
        left_token[i] = 0
        log(f"pass to the next position: {g.current_neddle[i]}", c_frame=c_frame())
    if g.current_neddle[i] > g.V:
        g.current_neddle[i] -= g.V


def do_read(index, left_token, ro: ReadOutput):
    if g.left_read_size[index] == 0:
        return
    obj_id = g.current_read_obj[index]
    size = g.obj_size[obj_id]

    for s in range(g.left_read_size[index], 0, -1):
        if g.if_last_read[index]:
            cost = max(math.ceil(g.last_read_cost[index] * 0.8), 16)
        else:
            cost = g.BASE_READ_COST

        if left_token[index] < cost:
            left_token[index] = 0
            return

        n_th_block = g.current_neddle[index] - g.next_position[index]
        g.new_obj_blocks[g.current_read_obj[index]] |= 2 ** n_th_block
        # log(f"read_position: {g.current_neddle[index]}", c_frame=c_frame())
        ro.add_read(index)

        g.left_read_size[index] -= 1
        g.if_last_read[index] = True
        g.last_read_cost[index] = cost
        left_token[index] -= cost
        g.current_neddle[index] += 1
        if g.current_neddle[index] == g.V + 1:
            g.current_neddle[index] = 1

    # read finished
    g.current_read_obj[index] = 0

    if g.new_obj_blocks[obj_id] == (2 ** size - 1):
        log(f"current read all blocks, emit all", c_frame=c_frame())
        ro.add_finished_request(g.request_id_dict[obj_id])
        ro.add_finished_request(g.new_id_dict[obj_id])
        g.request_id_dict[obj_id] = []
        g.new_id_dict[obj_id] = []
        for i in range(len(g.current_neddle)):
            if g.current_read_obj[i] == obj_id:
                g.current_read_obj[i] = 0
                g.left_read_size[i] = 0
    else:
        log(
            f"request id dict is locked, obj: {obj_id} {g.request_id_dict[obj_id]}",
            mode=ERROR,
            c_frame=c_frame(),
        )
        ro.add_finished_request(g.request_id_dict[obj_id])
        g.request_id_dict[obj_id] = deepcopy(g.new_id_dict[obj_id])
        g.new_id_dict[obj_id] = []


def calc_distance(position, current_position):
    if position >= current_position:
        return position - current_position
    else:
        return g.V - current_position + position


def read_action():
    n_read, read_req = read_input()
    ro = ReadOutput(g.N)

    rt.set_start_time()
    for req_id, obj_id in read_req[:]:
        # log(f"request id: {req_id}, obj_id: {obj_id}", c_frame=c_frame())
        g.new_id_dict[obj_id].append(req_id)
        copys = g.write_dict[obj_id]

        for copy in copys:
            tag, size, pos, index = copy
            g.request_data_list[index].insert(pos, obj_id)
        g.new_obj_blocks[obj_id] = 0
        g.obj_size[obj_id] = size
    rt.record_time("variable init")

    # left_size = sum([sum(g.request_id_dict[i]) for i in range(len(g.request_id_dict))])
    # log(f"left size: {left_size}", mode=ERROR, c_frame=c_frame())

    rt.set_start_time
    left_token = [g.G for i in range(g.N + 1)]
    request_size = [
        g.V + 1 if i == 0 else len(g.request_data_list[i].pos_list)
        for i in range(len(g.request_data_list))
    ]
    sorted_indices = sorted(range(len(request_size)), key=lambda i: request_size[i])
    request_size = [request_size[i] for i in sorted_indices]
    selected_list = sorted_indices
    rt.record_time("sort request")
    for i in selected_list[:-1]:
        # log(f"current index: {i}", mode=WARNING, new_line=True, c_frame=c_frame())
        count = 0
        obj_id = 0
        while True:
            count += 1
            # log(f"loop count: {count}")
            # read the left size
            # log(f"current position: {g.current_neddle[i]}, current read_obj: {g.current_read_obj[i]}", c_frame=c_frame())
            # log(
            #     f"left pass size: {g.left_pass_size[i]}, left read size: {g.left_read_size[i]}, left token: {left_token[i]}",
            #     c_frame=c_frame(),
            # )
            rt.set_start_time
            if g.left_pass_size[i]:
                do_pass(i, left_token, ro)
                # log(f"left pass size: {g.left_pass_size[i]}", c_frame=c_frame())
                if g.left_pass_size[i]:
                    break
            rt.record_time("do pass")

            rt.set_start_time()
            if g.left_read_size[i]:
                do_read(i, left_token, ro)
                # log(f"left read size: {g.left_read_size[i]}", c_frame=c_frame())
                if g.left_read_size[i]:
                    break
                # if g.left_read_size[i]: break
            rt.record_time("do read")

            if len(g.request_data_list[i].pos_list) == 0:
                break
            rt.set_start_time()
            if g.current_read_obj[i] == 0:
                # find the next obj to read, and move to the next position
                next_position_index = find_larger_pos(
                    g.request_data_list[i].pos_list, g.current_neddle[i]
                )

                pos = (g.request_data_list[i].pos_list[next_position_index],)
                obj_id = g.request_data_list[i].obj_id_list[next_position_index]
                g.next_position[i] = g.request_data_list[i].pos_list[
                    next_position_index
                ]

                # log(f"current position: {g.current_neddle[i]}", c_frame=c_frame())
                # log(f"find next read position: {g.next_position[i]}", c_frame=c_frame())
                pass_size = calc_distance(g.next_position[i], g.current_neddle[i])
                # if pass_size is larger than the token, then jump to the next position
                # log(
                #     f"calcuated pass size: {pass_size}, left_token: {left_token[i]}",
                #     c_frame=c_frame(),
                # )
                if pass_size <= g.G - g.BASE_READ_COST:
                    g.left_pass_size[i] = pass_size
                    set_request_volume(obj_id, i)
                    # log(
                    #     f"pass size: {pass_size}, pass to the next position: {g.next_position[i]}",
                    #     c_frame=c_frame(),
                    # )
                    continue
                elif (
                    g.G + left_token[i] - g.BASE_READ_COST
                    >= pass_size
                    >= g.G - g.BASE_READ_COST
                ):
                    if left_token[i] == g.G:
                        # log(
                        #     f"jump size {pass_size}, do jump: {g.next_position[i]}",
                        #     c_frame=c_frame(),
                        # )
                        do_jump(i, left_token, g.next_position[i], ro)
                        set_request_volume(obj_id, i)
                        break
                    else:
                        # log(
                        #     f"no token and pass size low, do pass:{g.next_position[i]}",
                        #     c_frame=c_frame(),
                        # )
                        g.left_pass_size[i] = pass_size
                        set_request_volume(obj_id, i)
                        continue

                elif g.G + left_token[i] - g.BASE_READ_COST <= pass_size:
                    if left_token[i] == g.G:
                        # log(
                        #     f"far, jump to next position: {g.next_position[i]}",
                        #     c_frame=c_frame(),
                        # )
                        set_request_volume(obj_id, i)
                        do_jump(i, left_token, g.next_position[i], ro)
                    else:
                        pass
                        # log(
                        #     f"far and no enough token",
                        #     c_frame=c_frame(),
                        # )
                    break
            rt.record_time("find next read position")

    ro.print_info()
