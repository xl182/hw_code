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

    for copy in copys:
        tag, size, pos, index = copy
        g.request_pos_list[index].delete(pos)
        g.disk_obj[index][pos] = 0
    g.left_read_size[volume_index] = size
    g.current_read_obj[volume_index] = obj_id
    # log(f"set request volume obj_id: {obj_id}, index: {volume_index}, position: {read_position}",c_frame=c_frame(),)


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
        # log(f"pass to the next position: {g.current_neddle[i]}", c_frame=c_frame())
    else:
        g.left_pass_size[i] = g.left_pass_size[i] - left_token[i]
        ro.add_pass(i, left_token[i])
        g.current_neddle[i] += left_token[i]
        left_token[i] = 0
        # log(f"pass to the next position: {g.current_neddle[i]}", c_frame=c_frame())
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
        # # log(f"read_position: {g.current_neddle[index]}", c_frame=c_frame())
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
        # log(f"current read all blocks, emit all", c_frame=c_frame())
        ro.add_finished_request(g.request_id_dict[obj_id])
        ro.add_finished_request(g.new_id_dict[obj_id])
        g.request_id_dict[obj_id] = []
        g.new_id_dict[obj_id] = []
        
        g.current_read_obj[index] = 0
        g.left_read_size[index] = 0
    else:
        # log(
        #     f"request id dict is locked, obj: {obj_id} {g.request_id_dict[obj_id]}",
        #     mode=ERROR,
        #     c_frame=c_frame(),
        # )
        ro.add_finished_request(g.request_id_dict[obj_id])
        g.request_id_dict[obj_id] = deepcopy(g.new_id_dict[obj_id])
        g.new_id_dict[obj_id] = []


def calc_distance(position, current_position):
    if position >= current_position:
        return position - current_position
    else:
        return g.V - current_position + position


def read_action():
    # rt.set_start_time("read input")
    n_read, read_req = read_input()
    ro = ReadOutput(g.N)
    # rt.record_time("read input")

    # rt.set_start_time("variable init")
    for req_id, obj_id in read_req[:]:
        # log(f"request id: {req_id}, obj_id: {obj_id}", c_frame=c_frame())
        g.new_id_dict[obj_id].append(req_id)
        copys = g.write_dict[obj_id]
        for copy in copys:
            tag, size, pos, index = copy
            g.request_pos_list[index].insert(pos)
            g.disk_obj[index][pos] = obj_id
        g.new_obj_blocks[obj_id] = 0
        g.obj_size[obj_id] = size
    # rt.record_time("variable init")

    # rt.set_start_time("sort request")
    left_token = [g.G for i in range(g.N + 1)]
    request_size = [
        g.V + 1 if i == 0 else len(g.request_pos_list[i])
        for i in range(len(g.request_pos_list))
    ]
    sorted_indices = sorted(range(len(request_size)), key=lambda i: request_size[i])
    request_size = [request_size[i] for i in sorted_indices]
    selected_list = sorted_indices
    # rt.record_time("sort request")
    
    # rt.set_start_time("read loop")
    for i in selected_list[:-1]:
    # for i in range(1, g.N + 1):
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
            if g.left_pass_size[i]:
                # rt.set_start_time("do pass")
                do_pass(i, left_token, ro)
                # rt.record_time("do pass")
                # log(f"left pass size: {g.left_pass_size[i]}", c_frame=c_frame())
                if g.left_pass_size[i]:
                    break
            
            if g.left_read_size[i]:
                # rt.set_start_time("do read")
                do_read(i, left_token, ro)
                # log(f"left read size: {g.left_read_size[i]}", c_frame=c_frame())
                # rt.record_time("do read")
                if g.left_read_size[i]:
                    break
                # if g.left_read_size[i]: break

            if len(g.request_pos_list[i]) == 0:
                break
            # rt.set_start_time("find next read position")
            if g.current_read_obj[i] == 0:
                # find the next obj to read, and move to the next position
                g.next_position[i] = g.request_pos_list[i].find_next_position(g.current_neddle[i])
                obj_id = g.disk_obj[i][g.next_position[i]]

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
                    break
            # rt.record_time("find next read position")
    # rt.set_start_time("read output")
    ro.print_info()
    # rt.record_time("read output")
    
    # rt.record_time("read loop")
